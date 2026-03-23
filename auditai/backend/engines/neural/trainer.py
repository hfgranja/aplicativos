"""
Model Training Pipeline
=======================
Full training loop for the AuditAI neural models:
  • VulnDataset / FixDataset — PyTorch Dataset wrappers for vulnerability data
  • TrainingConfig — hyperparameter dataclass
  • TrainingMetrics — per-epoch metric tracking
  • ModelTrainer — orchestrates fine-tuning with EWC + replay

Usage::
    from engines.neural.trainer import ModelTrainer, TrainingConfig
    from engines.neural import (VulnerabilityKnowledgeBase, BigVulLoader,
                                 SWEBenchLoader, ContinualLearner)

    config = TrainingConfig(epochs=3, batch_size=16, learning_rate=2e-5)
    trainer = ModelTrainer(config=config, kb=kb, learner=learner)
    metrics = await trainer.train_from_sources(bigvul_loader, swb_loader)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hyperparameter config
# ---------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    # Model checkpoints
    checkpoint_dir: str = "./data/checkpoints"
    kb_path: str = "./data/vuln_kb"

    # Training hyperparameters
    epochs: int = 3
    batch_size: int = 16
    learning_rate: float = 2e-5
    max_seq_length: int = 512
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    gradient_clip: float = 1.0

    # EWC
    ewc_lambda: float = 0.4
    replay_ratio: float = 0.3      # fraction of batch drawn from replay buffer

    # Data limits (None = no limit)
    max_vuln_samples: int | None = 5000
    max_fix_samples: int | None = 2000

    # Evaluation
    eval_steps: int = 200           # evaluate every N optimizer steps
    save_steps: int = 500

    # Data sources to use
    use_bigvul: bool = True
    use_swebench: bool = True
    use_nvd: bool = True
    use_arxiv: bool = True
    nvd_keyword: str = "injection"
    arxiv_query: str = "vulnerability detection deep learning"


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@dataclass
class EpochMetrics:
    epoch: int
    loss: float
    accuracy: float | None = None
    f1: float | None = None
    vuln_tp: int = 0
    vuln_fp: int = 0
    vuln_fn: int = 0
    vuln_tn: int = 0
    fix_bleu: float | None = None
    elapsed_seconds: float = 0.0

    @property
    def precision(self) -> float | None:
        denom = self.vuln_tp + self.vuln_fp
        return self.vuln_tp / denom if denom else None

    @property
    def recall(self) -> float | None:
        denom = self.vuln_tp + self.vuln_fn
        return self.vuln_tp / denom if denom else None


@dataclass
class TrainingMetrics:
    model_name: str
    config: dict
    epochs: list[EpochMetrics] = field(default_factory=list)
    best_epoch: int = 0
    best_loss: float = float("inf")
    total_samples: int = 0
    total_time_seconds: float = 0.0
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def record_epoch(self, m: EpochMetrics) -> None:
        self.epochs.append(m)
        if m.loss < self.best_loss:
            self.best_loss = m.loss
            self.best_epoch = m.epoch

    def finish(self) -> None:
        self.finished_at = time.time()
        self.total_time_seconds = self.finished_at - self.started_at

    def summary(self) -> dict:
        return {
            "model": self.model_name,
            "epochs_run": len(self.epochs),
            "best_epoch": self.best_epoch,
            "best_loss": round(self.best_loss, 4),
            "total_samples": self.total_samples,
            "total_time_s": round(self.total_time_seconds, 1),
            "last_accuracy": self.epochs[-1].accuracy if self.epochs else None,
            "last_f1": self.epochs[-1].f1 if self.epochs else None,
        }


# ---------------------------------------------------------------------------
# PyTorch Dataset helpers (imported lazily to allow graceful fallback)
# ---------------------------------------------------------------------------

def _make_vuln_dataset(samples: list[dict], tokenizer, max_len: int):
    """
    Returns a torch.utils.data.Dataset for vulnerability classification.

    Each sample dict must have:
        code (str), label (int 0/1), cwe_ids (list[str])
    """
    try:
        import torch
        from torch.utils.data import Dataset

        class VulnDataset(Dataset):
            def __init__(self, samples, tokenizer, max_len):
                self.samples = samples
                self.tokenizer = tokenizer
                self.max_len = max_len

            def __len__(self):
                return len(self.samples)

            def __getitem__(self, idx):
                s = self.samples[idx]
                enc = self.tokenizer(
                    s["code"],
                    truncation=True,
                    padding="max_length",
                    max_length=self.max_len,
                    return_tensors="pt",
                )
                return {
                    "input_ids": enc["input_ids"].squeeze(0),
                    "attention_mask": enc["attention_mask"].squeeze(0),
                    "label": torch.tensor(s["label"], dtype=torch.float),
                }

        return VulnDataset(samples, tokenizer, max_len)
    except ImportError:
        return None


def _make_fix_dataset(samples: list[dict], tokenizer, max_len: int):
    """
    Returns a torch.utils.data.Dataset for fix synthesis (seq2seq).

    Each sample dict: before_code (str), after_code (str)
    """
    try:
        import torch
        from torch.utils.data import Dataset

        class FixDataset(Dataset):
            def __init__(self, samples, tokenizer, max_len):
                self.samples = samples
                self.tokenizer = tokenizer
                self.max_len = max_len

            def __len__(self):
                return len(self.samples)

            def __getitem__(self, idx):
                s = self.samples[idx]
                src = self.tokenizer(
                    f"fix: {s['before_code']}",
                    truncation=True,
                    padding="max_length",
                    max_length=self.max_len,
                    return_tensors="pt",
                )
                tgt = self.tokenizer(
                    s["after_code"],
                    truncation=True,
                    padding="max_length",
                    max_length=self.max_len,
                    return_tensors="pt",
                )
                labels = tgt["input_ids"].squeeze(0).clone()
                labels[labels == self.tokenizer.pad_token_id] = -100
                return {
                    "input_ids": src["input_ids"].squeeze(0),
                    "attention_mask": src["attention_mask"].squeeze(0),
                    "labels": labels,
                }

        return FixDataset(samples, tokenizer, max_len)
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# BLEU helper (no sacrebleu dependency)
# ---------------------------------------------------------------------------

def _simple_bleu(hypothesis: str, reference: str) -> float:
    """Unigram + bigram precision as a quick BLEU approximation."""
    hyp = hypothesis.split()
    ref = reference.split()
    if not hyp or not ref:
        return 0.0
    ref_counts: dict[str, int] = {}
    for w in ref:
        ref_counts[w] = ref_counts.get(w, 0) + 1
    uni_match = sum(min(hyp.count(w), ref_counts.get(w, 0)) for w in set(hyp))
    uni_prec = uni_match / len(hyp)
    if len(hyp) < 2:
        return uni_prec
    ref_bi: dict[tuple, int] = {}
    for i in range(len(ref) - 1):
        k = (ref[i], ref[i + 1])
        ref_bi[k] = ref_bi.get(k, 0) + 1
    bi_match = 0
    for i in range(len(hyp) - 1):
        k = (hyp[i], hyp[i + 1])
        if ref_bi.get(k, 0) > 0:
            bi_match += 1
            ref_bi[k] -= 1
    bi_prec = bi_match / (len(hyp) - 1)
    return (uni_prec * bi_prec) ** 0.5


# ---------------------------------------------------------------------------
# Model Evaluator
# ---------------------------------------------------------------------------

class ModelEvaluator:
    """Runs evaluation on a held-out slice of samples."""

    def evaluate_classifier(
        self,
        classifier,              # DeepVulnClassifier
        samples: list[dict],     # list of {code, label}
    ) -> dict[str, Any]:
        if not samples:
            return {}
        tp = fp = fn = tn = 0
        for s in samples:
            pred = classifier.predict(s["code"])
            predicted = 1 if pred.is_vulnerable else 0
            actual = int(s["label"])
            if predicted == 1 and actual == 1:
                tp += 1
            elif predicted == 1 and actual == 0:
                fp += 1
            elif predicted == 0 and actual == 1:
                fn += 1
            else:
                tn += 1
        total = tp + fp + fn + tn
        accuracy = (tp + tn) / total if total else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        }

    def evaluate_synthesizer(
        self,
        synthesizer,             # FixSynthesizer
        samples: list[dict],     # list of {before_code, after_code}
        n: int = 50,
    ) -> dict[str, Any]:
        if not samples:
            return {}
        bleu_scores = []
        for s in samples[:n]:
            result = synthesizer.synthesize(s["before_code"], "")
            if result.fixed_code:
                bleu_scores.append(_simple_bleu(result.fixed_code, s["after_code"]))
        avg_bleu = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0
        return {
            "bleu_approx": round(avg_bleu, 4),
            "samples_evaluated": len(bleu_scores),
        }


# ---------------------------------------------------------------------------
# Main Trainer
# ---------------------------------------------------------------------------

class ModelTrainer:
    """
    Orchestrates the full training pipeline:
      1. Load data from BigVul / SWE-bench loaders
      2. Ingest into VulnerabilityKnowledgeBase (embeddings)
      3. Fine-tune DeepVulnClassifier + FixSynthesizer via ContinualLearner
      4. Evaluate and return TrainingMetrics

    All torch operations are guarded — if torch is unavailable the trainer
    falls back to updating only the knowledge base (no gradient-based training).
    """

    def __init__(
        self,
        config: TrainingConfig | None = None,
        kb=None,        # VulnerabilityKnowledgeBase
        learner=None,   # ContinualLearner
    ):
        self.config = config or TrainingConfig()
        self.kb = kb
        self.learner = learner
        self._evaluator = ModelEvaluator()
        self._torch_available = self._check_torch()

    @staticmethod
    def _check_torch() -> bool:
        try:
            import torch  # noqa: F401
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def train_from_sources(
        self,
        bigvul_loader=None,
        swb_loader=None,
        nvd_connector=None,
        arxiv_connector=None,
    ) -> list[TrainingMetrics]:
        """
        Full ingestion + training run.
        Returns a list of TrainingMetrics (one per model trained).
        """
        all_metrics: list[TrainingMetrics] = []
        vuln_samples: list[dict] = []
        fix_samples: list[dict] = []

        # ── 1. Collect vulnerability samples ──────────────────────────
        if self.config.use_bigvul and bigvul_loader is not None:
            logger.info("Loading BigVul samples…")
            raw = bigvul_loader.load_samples(
                max_samples=self.config.max_vuln_samples or 5000
            )
            for s in raw:
                vuln_samples.append({
                    "code": s.code,
                    "label": s.label,
                    "cwe_ids": s.cwe_ids,
                    "severity": s.severity,
                })
            logger.info("Loaded %d BigVul samples", len(raw))

        if self.config.use_swebench and swb_loader is not None:
            logger.info("Loading SWE-bench samples…")
            raw_fix = swb_loader.load_samples(
                max_samples=self.config.max_fix_samples or 2000
            )
            for s in raw_fix:
                if s.before_code and s.after_code:
                    fix_samples.append({
                        "before_code": s.before_code,
                        "after_code": s.after_code,
                        "repo": s.repo,
                        "issue": s.issue_text,
                    })
            logger.info("Loaded %d SWE-bench fix pairs", len(raw_fix))

        # ── 2. Ingest into knowledge base ──────────────────────────────
        if self.kb is not None:
            await self._ingest_knowledge_base(nvd_connector, arxiv_connector)
            # Add fix patterns from SWE-bench
            for i, fp in enumerate(fix_samples[:500]):
                self.kb.add_fix_pattern(
                    fix_id=f"swb_{i}",
                    vuln_description=fp.get("issue", "bug fix")[:200],
                    before_code=fp["before_code"],
                    after_code=fp["after_code"],
                    source="swebench",
                )
            self.kb.save()
            logger.info("Knowledge base saved. Stats: %s", self.kb.stats())

        # ── 3. Fine-tune classifier ────────────────────────────────────
        if vuln_samples and self._torch_available:
            metrics = await self._train_classifier(vuln_samples)
            all_metrics.append(metrics)

        # ── 4. Fine-tune fix synthesizer ───────────────────────────────
        if fix_samples and self._torch_available:
            metrics = await self._train_synthesizer(fix_samples)
            all_metrics.append(metrics)

        if not self._torch_available:
            logger.warning(
                "torch not available — skipping gradient-based training. "
                "Knowledge base was still updated."
            )

        return all_metrics

    async def train_on_finding(
        self,
        code: str,
        label: int,
        fix_before: str | None = None,
        fix_after: str | None = None,
        cwe_id: str | None = None,
    ) -> None:
        """
        Online learning: incorporate a single new labeled example.
        Delegates to ContinualLearner if available.
        """
        if self.learner is None:
            return
        sample: dict[str, Any] = {"code": code, "label": label}
        if cwe_id:
            sample["cwe_ids"] = [cwe_id]
        fix_data = None
        if fix_before and fix_after:
            fix_data = {"before_code": fix_before, "after_code": fix_after}
        try:
            self.learner.learn_from_new_data([sample], fix_samples=[fix_data] if fix_data else [])
        except Exception as exc:
            logger.warning("Online learning step failed: %s", exc)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _ingest_knowledge_base(self, nvd_connector, arxiv_connector) -> None:
        if self.kb is None:
            return
        tasks = []
        if nvd_connector and self.config.use_nvd:
            tasks.append(self.kb.ingest_nvd(nvd_connector, keyword=self.config.nvd_keyword))
        if arxiv_connector and self.config.use_arxiv:
            tasks.append(self.kb.ingest_arxiv(arxiv_connector, query=self.config.arxiv_query))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _train_classifier(self, samples: list[dict]) -> TrainingMetrics:
        """Fine-tune DeepVulnClassifier on vulnerability samples."""
        from .models import ModelRegistry
        config = self.config
        metrics = TrainingMetrics(
            model_name="DeepVulnClassifier",
            config=asdict(config),
            total_samples=len(samples),
        )

        try:
            import torch
            from torch.utils.data import DataLoader
            from torch.optim import AdamW

            registry = ModelRegistry.get_instance()
            classifier = registry.get_classifier()

            if not classifier._loaded or classifier._model is None:
                logger.info("Classifier backbone not loaded — skipping gradient training")
                metrics.finish()
                return metrics

            # Split train/eval (90/10)
            split = max(1, int(len(samples) * 0.9))
            train_samples = samples[:split]
            eval_samples = samples[split:]

            tokenizer = classifier._tokenizer
            ds = _make_vuln_dataset(train_samples, tokenizer, config.max_seq_length)
            if ds is None:
                metrics.finish()
                return metrics

            loader = DataLoader(ds, batch_size=config.batch_size, shuffle=True)
            optimizer = AdamW(
                classifier._model.parameters(),
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
            )

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            classifier._model.to(device)
            classifier._model.train()

            total_steps = len(loader) * config.epochs
            warmup_steps = int(total_steps * config.warmup_ratio)

            for epoch in range(config.epochs):
                t0 = time.time()
                epoch_loss = 0.0
                step = 0
                for batch in loader:
                    optimizer.zero_grad()
                    input_ids = batch["input_ids"].to(device)
                    attn_mask = batch["attention_mask"].to(device)
                    labels = batch["label"].to(device)

                    outputs = classifier._model(input_ids, attn_mask)
                    vuln_logits = outputs["vuln_logits"].squeeze(-1)
                    loss = torch.nn.functional.binary_cross_entropy_with_logits(
                        vuln_logits, labels
                    )

                    # EWC penalty
                    if (
                        self.learner is not None
                        and self.learner.ewc is not None
                        and self.learner.ewc._fisher_params
                    ):
                        loss = loss + self.learner.ewc.penalty(classifier._model)

                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(
                        classifier._model.parameters(), config.gradient_clip
                    )
                    optimizer.step()

                    # Learning rate warmup (linear)
                    global_step = epoch * len(loader) + step
                    if global_step < warmup_steps:
                        lr_scale = (global_step + 1) / warmup_steps
                        for pg in optimizer.param_groups:
                            pg["lr"] = config.learning_rate * lr_scale

                    epoch_loss += loss.item()
                    step += 1

                avg_loss = epoch_loss / max(step, 1)
                elapsed = time.time() - t0

                # Evaluate
                eval_result = self._evaluator.evaluate_classifier(classifier, eval_samples)
                em = EpochMetrics(
                    epoch=epoch,
                    loss=avg_loss,
                    accuracy=eval_result.get("accuracy"),
                    f1=eval_result.get("f1"),
                    vuln_tp=eval_result.get("tp", 0),
                    vuln_fp=eval_result.get("fp", 0),
                    vuln_fn=eval_result.get("fn", 0),
                    vuln_tn=eval_result.get("tn", 0),
                    elapsed_seconds=elapsed,
                )
                metrics.record_epoch(em)
                logger.info(
                    "Epoch %d/%d | loss=%.4f acc=%.4f f1=%.4f (%.1fs)",
                    epoch + 1, config.epochs, avg_loss,
                    eval_result.get("accuracy", 0), eval_result.get("f1", 0), elapsed,
                )

                # Save checkpoint
                if (epoch + 1) % max(1, config.save_steps // len(loader)) == 0:
                    self._save_classifier(classifier, epoch)

                # Update EWC Fisher after each epoch
                if self.learner is not None:
                    try:
                        self.learner.ewc.compute_fisher(
                            classifier._model, [(s["code"], s["label"]) for s in train_samples[:100]]
                        )
                    except Exception as exc:
                        logger.warning("Fisher update failed: %s", exc)

            classifier._model.eval()

        except Exception as exc:
            logger.error("Classifier training failed: %s", exc, exc_info=True)

        metrics.finish()
        logger.info("Classifier training done: %s", metrics.summary())
        return metrics

    async def _train_synthesizer(self, samples: list[dict]) -> TrainingMetrics:
        """Fine-tune FixSynthesizer (CodeT5) on fix pairs."""
        from .models import ModelRegistry
        config = self.config
        metrics = TrainingMetrics(
            model_name="FixSynthesizer",
            config=asdict(config),
            total_samples=len(samples),
        )

        try:
            import torch
            from torch.utils.data import DataLoader
            from torch.optim import AdamW

            registry = ModelRegistry.get_instance()
            synthesizer = registry.get_synthesizer()

            if not synthesizer._loaded or synthesizer._model is None:
                logger.info("Synthesizer model not loaded — skipping gradient training")
                metrics.finish()
                return metrics

            split = max(1, int(len(samples) * 0.9))
            train_samples = samples[:split]
            eval_samples = samples[split:]

            tokenizer = synthesizer._tokenizer
            ds = _make_fix_dataset(train_samples, tokenizer, config.max_seq_length)
            if ds is None:
                metrics.finish()
                return metrics

            loader = DataLoader(ds, batch_size=max(1, config.batch_size // 2), shuffle=True)
            optimizer = AdamW(
                synthesizer._model.parameters(),
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
            )

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            synthesizer._model.to(device)
            synthesizer._model.train()

            for epoch in range(config.epochs):
                t0 = time.time()
                epoch_loss = 0.0
                step = 0
                for batch in loader:
                    optimizer.zero_grad()
                    out = synthesizer._model(
                        input_ids=batch["input_ids"].to(device),
                        attention_mask=batch["attention_mask"].to(device),
                        labels=batch["labels"].to(device),
                    )
                    loss = out.loss
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(
                        synthesizer._model.parameters(), config.gradient_clip
                    )
                    optimizer.step()
                    epoch_loss += loss.item()
                    step += 1

                avg_loss = epoch_loss / max(step, 1)
                elapsed = time.time() - t0
                eval_result = self._evaluator.evaluate_synthesizer(synthesizer, eval_samples)
                em = EpochMetrics(
                    epoch=epoch,
                    loss=avg_loss,
                    fix_bleu=eval_result.get("bleu_approx"),
                    elapsed_seconds=elapsed,
                )
                metrics.record_epoch(em)
                logger.info(
                    "Synth epoch %d/%d | loss=%.4f bleu≈%.4f (%.1fs)",
                    epoch + 1, config.epochs, avg_loss,
                    eval_result.get("bleu_approx", 0), elapsed,
                )

            synthesizer._model.eval()

        except Exception as exc:
            logger.error("Synthesizer training failed: %s", exc, exc_info=True)

        metrics.finish()
        logger.info("Synthesizer training done: %s", metrics.summary())
        return metrics

    def _save_classifier(self, classifier, epoch: int) -> None:
        try:
            import torch
            ckpt_dir = Path(self.config.checkpoint_dir)
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            path = ckpt_dir / f"classifier_epoch{epoch}.pt"
            torch.save(classifier._model.state_dict(), str(path))
            logger.info("Saved classifier checkpoint: %s", path)
        except Exception as exc:
            logger.warning("Checkpoint save failed: %s", exc)
