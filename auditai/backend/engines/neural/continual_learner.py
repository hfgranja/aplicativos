"""
Continual Learning — Catastrophic Forgetting Prevention
=======================================================
Models that learn from new vulnerability data must not forget previously learned
patterns. This module implements two complementary strategies:

  ElasticWeightConsolidation (EWC)
    - After learning task T_n, compute Fisher information diagonal F
    - Penalise future updates that move parameters far from θ*_n
    - Loss: L_new(θ) + λ/2 * Σ_i F_i (θ_i − θ*_i)²
    - Reference: Kirkpatrick et al. 2017 (https://arxiv.org/abs/1612.00796)

  ExperienceReplayBuffer
    - Store a fixed-size random sample of past (code, label) examples
    - Interleave past samples with new data during fine-tuning
    - Prevents the model from overfitting to the distribution of new examples
    - Uses reservoir sampling to maintain unbiased representation

  ContinualLearner
    - Combines EWC + Replay into a single train() interface
    - Integrates with DeepVulnClassifier and FixSynthesizer checkpoints
    - Records task history for audit trail
"""

from __future__ import annotations

import copy
import json
import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _torch():
    try:
        import torch
        return torch
    except ImportError:
        return None


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class ReplayExample:
    code: str
    label: int            # 0 = non-vulnerable, 1 = vulnerable
    cwe_labels: list[int] = field(default_factory=list)
    source: str = "unknown"
    added_at: float = field(default_factory=time.time)


@dataclass
class TaskRecord:
    task_id: str
    description: str
    num_samples: int
    train_loss: float
    eval_accuracy: float
    ewc_penalty: float
    timestamp: float = field(default_factory=time.time)


# ── Experience Replay Buffer ───────────────────────────────────────────────────

class ExperienceReplayBuffer:
    """
    Reservoir sampling buffer maintaining a fixed-size unbiased sample
    of all previously seen examples.

    Reservoir sampling guarantees that each of the N examples seen so far
    has equal probability (capacity/N) of being in the buffer.
    """

    def __init__(self, capacity: int = 2_000):
        self.capacity = capacity
        self._buffer: list[ReplayExample] = []
        self._n_seen: int = 0

    def add(self, example: ReplayExample) -> None:
        self._n_seen += 1
        if len(self._buffer) < self.capacity:
            self._buffer.append(example)
        else:
            # Reservoir sampling: replace with probability capacity/n_seen
            idx = random.randint(0, self._n_seen - 1)
            if idx < self.capacity:
                self._buffer[idx] = example

    def add_batch(self, examples: list[ReplayExample]) -> None:
        for ex in examples:
            self.add(ex)

    def sample(self, n: int) -> list[ReplayExample]:
        n = min(n, len(self._buffer))
        return random.sample(self._buffer, n) if n > 0 else []

    def __len__(self) -> int:
        return len(self._buffer)

    def __repr__(self) -> str:
        return f"<ExperienceReplayBuffer size={len(self._buffer)}/{self.capacity} seen={self._n_seen}>"

    def to_dict(self) -> dict:
        return {
            "capacity": self.capacity,
            "n_seen": self._n_seen,
            "buffer": [
                {
                    "code": ex.code[:500],
                    "label": ex.label,
                    "cwe_labels": ex.cwe_labels,
                    "source": ex.source,
                }
                for ex in self._buffer
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExperienceReplayBuffer":
        buf = cls(capacity=data["capacity"])
        buf._n_seen = data["n_seen"]
        buf._buffer = [
            ReplayExample(
                code=ex["code"],
                label=ex["label"],
                cwe_labels=ex.get("cwe_labels", []),
                source=ex.get("source", "unknown"),
            )
            for ex in data.get("buffer", [])
        ]
        return buf


# ── Elastic Weight Consolidation ───────────────────────────────────────────────

class ElasticWeightConsolidation:
    """
    EWC regularisation for PyTorch models.

    Usage:
        ewc = ElasticWeightConsolidation(model, lambda_ewc=0.4)
        ewc.compute_fisher(dataloader, n_samples=200)   # after training task T_n
        # During training on T_{n+1}:
        loss = criterion(outputs, labels) + ewc.penalty()
    """

    def __init__(self, model, lambda_ewc: float = 0.4):
        self._model = model
        self.lambda_ewc = lambda_ewc
        self._params_mean: dict[str, Any] = {}    # θ* (consolidated parameters)
        self._fisher_diag: dict[str, Any] = {}    # F (diagonal Fisher information)

    def compute_fisher(self, examples: list[ReplayExample], tokenizer, n_samples: int = 200) -> None:
        """
        Estimate the diagonal Fisher information matrix using n_samples examples.
        Fisher diagonal F_i ≈ E[(∂ log p(y|x) / ∂ θ_i)²]
        """
        torch = _torch()
        if torch is None or self._model is None:
            logger.warning("EWC: torch unavailable, skipping Fisher computation")
            return

        import torch.nn.functional as F

        # Snapshot current optimal parameters θ*
        self._params_mean = {
            n: p.clone().detach()
            for n, p in self._model.named_parameters()
            if p.requires_grad
        }

        # Initialise Fisher diagonal accumulators
        fisher = {
            n: torch.zeros_like(p)
            for n, p in self._model.named_parameters()
            if p.requires_grad
        }

        self._model.eval()
        sample = random.sample(examples, min(n_samples, len(examples)))

        for ex in sample:
            try:
                enc = tokenizer(
                    ex.code,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding="max_length",
                )
                device = next(self._model.parameters()).device
                enc = {k: v.to(device) for k, v in enc.items()}
                label = torch.tensor([[float(ex.label)]], device=device)

                self._model.zero_grad()
                out = self._model(enc["input_ids"], enc["attention_mask"])
                vuln_prob = torch.sigmoid(out["vuln_logit"])
                loss = F.binary_cross_entropy(vuln_prob, label)
                loss.backward()

                for n, p in self._model.named_parameters():
                    if p.requires_grad and p.grad is not None:
                        fisher[n] += p.grad.data.clone().pow(2)
            except Exception:
                continue

        n = max(len(sample), 1)
        self._fisher_diag = {n: (f / n) for n, f in fisher.items()}
        logger.info(
            "EWC Fisher computed on %d samples. λ=%.3f. Params consolidated: %d",
            len(sample), self.lambda_ewc, len(self._params_mean),
        )

    def penalty(self):
        """EWC regularisation term to add to the training loss."""
        torch = _torch()
        if torch is None or not self._fisher_diag:
            return 0.0

        penalty = torch.tensor(0.0)
        device = next(iter(self._fisher_diag.values())).device if self._fisher_diag else None
        if device:
            penalty = penalty.to(device)

        for name, param in self._model.named_parameters():
            if name in self._fisher_diag:
                f = self._fisher_diag[name]
                mean = self._params_mean[name]
                penalty += (f * (param - mean).pow(2)).sum()

        return self.lambda_ewc / 2.0 * penalty

    def has_fisher(self) -> bool:
        return bool(self._fisher_diag)

    def save(self, path: str) -> None:
        torch = _torch()
        if torch is None:
            return
        torch.save({
            "params_mean": self._params_mean,
            "fisher_diag": self._fisher_diag,
            "lambda_ewc": self.lambda_ewc,
        }, path)

    def load(self, path: str) -> None:
        torch = _torch()
        if torch is None or not Path(path).exists():
            return
        data = torch.load(path, map_location="cpu")
        self._params_mean = data["params_mean"]
        self._fisher_diag = data["fisher_diag"]
        self.lambda_ewc = data["lambda_ewc"]


# ── Continual Learner ──────────────────────────────────────────────────────────

class ContinualLearner:
    """
    Combines EWC + Experience Replay to enable online learning from new
    vulnerability data while preserving existing knowledge.

    Each call to learn_from_new_data():
      1. Creates a mixed batch (new samples + replay samples)
      2. Fine-tunes the model with EWC regularisation
      3. Updates Fisher information after training
      4. Adds new samples to the replay buffer
      5. Records the task in history

    Supports both DeepVulnClassifier and FixSynthesizer.
    """

    def __init__(
        self,
        vuln_classifier=None,
        fix_synthesizer=None,
        replay_capacity: int = 2_000,
        lambda_ewc: float = 0.4,
        learning_rate: float = 2e-5,
        checkpoint_dir: str | None = None,
    ):
        self._vuln_clf = vuln_classifier
        self._fix_syn = fix_synthesizer
        self.replay = ExperienceReplayBuffer(capacity=replay_capacity)
        self._ewc: ElasticWeightConsolidation | None = None
        self.lambda_ewc = lambda_ewc
        self.lr = learning_rate
        self._checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        self._task_history: list[TaskRecord] = []

        if self._checkpoint_dir:
            self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
            self._load_state()

    def learn_from_new_data(
        self,
        new_examples: list[ReplayExample],
        task_description: str = "online_learning",
        n_epochs: int = 3,
        batch_size: int = 16,
        replay_ratio: float = 0.3,
    ) -> TaskRecord:
        """
        Fine-tune the vulnerability classifier on new examples with EWC + replay.

        Parameters
        ----------
        new_examples   : New labelled code samples to learn from
        task_description : Human-readable description for audit trail
        n_epochs       : Training epochs over the new data
        batch_size     : Mini-batch size (new + replay)
        replay_ratio   : Fraction of each batch drawn from replay buffer
        """
        torch = _torch()
        if torch is None or self._vuln_clf is None:
            logger.warning("ContinualLearner: torch/model unavailable, skipping training")
            self.replay.add_batch(new_examples)
            return TaskRecord(
                task_id=f"task_{len(self._task_history)+1}",
                description=task_description,
                num_samples=len(new_examples),
                train_loss=0.0,
                eval_accuracy=0.0,
                ewc_penalty=0.0,
            )

        import torch.nn.functional as F

        if not self._vuln_clf._load():
            logger.warning("ContinualLearner: classifier not loaded, skipping")
            self.replay.add_batch(new_examples)
            return self._make_task_record(task_description, len(new_examples), 0.0, 0.0, 0.0)

        model = self._vuln_clf._model
        tokenizer = self._vuln_clf._tokenizer
        device = next(model.parameters()).device

        # Initialise EWC on first task or reload
        if self._ewc is None:
            self._ewc = ElasticWeightConsolidation(model, lambda_ewc=self.lambda_ewc)

        optimizer = torch.optim.AdamW(model.parameters(), lr=self.lr)
        model.train()

        total_loss = 0.0
        n_batches = 0
        n_replay_per_batch = int(batch_size * replay_ratio)
        n_new_per_batch = batch_size - n_replay_per_batch

        for epoch in range(n_epochs):
            random.shuffle(new_examples)
            for start in range(0, len(new_examples), n_new_per_batch):
                batch_new = new_examples[start : start + n_new_per_batch]
                batch_replay = self.replay.sample(n_replay_per_batch)
                batch = batch_new + batch_replay

                if not batch:
                    continue

                optimizer.zero_grad()
                batch_loss = torch.tensor(0.0, device=device, requires_grad=True)
                valid = 0

                for ex in batch:
                    try:
                        enc = tokenizer(
                            ex.code,
                            return_tensors="pt",
                            truncation=True,
                            max_length=512,
                            padding="max_length",
                        )
                        enc = {k: v.to(device) for k, v in enc.items()}
                        label = torch.tensor([[float(ex.label)]], device=device)
                        out = model(enc["input_ids"], enc["attention_mask"])
                        vuln_prob = torch.sigmoid(out["vuln_logit"])
                        sample_loss = F.binary_cross_entropy(vuln_prob, label)
                        batch_loss = batch_loss + sample_loss
                        valid += 1
                    except Exception:
                        continue

                if valid > 0:
                    batch_loss = batch_loss / valid
                    ewc_penalty = self._ewc.penalty() if self._ewc.has_fisher() else torch.tensor(0.0)
                    combined = batch_loss + (ewc_penalty if isinstance(ewc_penalty, torch.Tensor) else torch.tensor(ewc_penalty))
                    combined.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    total_loss += float(batch_loss)
                    n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)

        # Update Fisher information with new examples
        all_examples = new_examples + self.replay.sample(min(200, len(self.replay)))
        if all_examples:
            self._ewc.compute_fisher(all_examples, tokenizer, n_samples=min(200, len(all_examples)))

        # Add new examples to replay buffer
        self.replay.add_batch(new_examples)

        # Evaluate on replay sample
        accuracy = self._evaluate(model, tokenizer, device, self.replay.sample(100))

        model.eval()

        task = self._make_task_record(task_description, len(new_examples), avg_loss, accuracy, 0.0)
        self._task_history.append(task)

        if self._checkpoint_dir:
            self._save_state()

        logger.info(
            "ContinualLearner: task='%s' samples=%d loss=%.4f accuracy=%.3f",
            task_description, len(new_examples), avg_loss, accuracy,
        )
        return task

    def _evaluate(self, model, tokenizer, device, examples: list[ReplayExample]) -> float:
        """Quick accuracy estimate on a sample."""
        if not examples:
            return 0.0
        torch = _torch()
        if torch is None:
            return 0.0
        import torch as t
        correct = 0
        model.eval()
        with t.no_grad():
            for ex in examples[:50]:
                try:
                    enc = tokenizer(
                        ex.code, return_tensors="pt", truncation=True,
                        max_length=512, padding="max_length",
                    )
                    enc = {k: v.to(device) for k, v in enc.items()}
                    out = model(enc["input_ids"], enc["attention_mask"])
                    pred = int(t.sigmoid(out["vuln_logit"]).squeeze() > 0.5)
                    if pred == ex.label:
                        correct += 1
                except Exception:
                    continue
        return correct / min(len(examples), 50)

    def _make_task_record(
        self, description: str, num_samples: int,
        loss: float, accuracy: float, ewc_penalty: float
    ) -> TaskRecord:
        return TaskRecord(
            task_id=f"task_{len(self._task_history)+1}",
            description=description,
            num_samples=num_samples,
            train_loss=loss,
            eval_accuracy=accuracy,
            ewc_penalty=ewc_penalty,
        )

    def task_history(self) -> list[dict]:
        return [
            {
                "task_id": t.task_id,
                "description": t.description,
                "num_samples": t.num_samples,
                "train_loss": t.train_loss,
                "eval_accuracy": t.eval_accuracy,
                "timestamp": t.timestamp,
            }
            for t in self._task_history
        ]

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_state(self) -> None:
        if self._checkpoint_dir is None:
            return
        # Save replay buffer
        with open(self._checkpoint_dir / "replay_buffer.json", "w") as f:
            json.dump(self.replay.to_dict(), f)
        # Save EWC Fisher
        if self._ewc is not None and self._ewc.has_fisher():
            self._ewc.save(str(self._checkpoint_dir / "ewc_fisher.pt"))
        # Save task history
        with open(self._checkpoint_dir / "task_history.json", "w") as f:
            json.dump(self.task_history(), f, indent=2)
        # Save model checkpoints
        if self._vuln_clf is not None:
            self._vuln_clf.save_checkpoint(str(self._checkpoint_dir / "vuln_classifier.pt"))
        if self._fix_syn is not None:
            self._fix_syn.save_checkpoint(str(self._checkpoint_dir / "fix_synthesizer.pt"))

    def _load_state(self) -> None:
        if self._checkpoint_dir is None:
            return
        replay_path = self._checkpoint_dir / "replay_buffer.json"
        if replay_path.exists():
            with open(replay_path) as f:
                self.replay = ExperienceReplayBuffer.from_dict(json.load(f))
        history_path = self._checkpoint_dir / "task_history.json"
        if history_path.exists():
            with open(history_path) as f:
                raw = json.load(f)
            self._task_history = [
                TaskRecord(
                    task_id=r["task_id"],
                    description=r["description"],
                    num_samples=r["num_samples"],
                    train_loss=r["train_loss"],
                    eval_accuracy=r["eval_accuracy"],
                    ewc_penalty=r.get("ewc_penalty", 0.0),
                    timestamp=r["timestamp"],
                )
                for r in raw
            ]
        logger.info(
            "ContinualLearner state loaded: %d replay samples, %d tasks",
            len(self.replay), len(self._task_history),
        )
