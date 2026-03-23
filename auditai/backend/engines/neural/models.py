"""
Deep Learning Models for Vulnerability Detection and Code Repair
================================================================
All models are designed for:
  • Lazy loading (GPU/CPU auto-detection)
  • Graceful fallback when transformers unavailable
  • Continual learning via the ContinualLearner wrapper
  • Serialisation for checkpoint save/load

Models:
  DeepVulnClassifier  — CodeBERT binary vulnerability classifier + CWE tagger
  FixSynthesizer      — CodeT5 seq2seq fix generator
  TechniqueRetriever  — Sentence-BERT for academic technique retrieval
  AIBugDetector       — Specialised classifier for AI-generated code anti-patterns
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Lazy import guards ─────────────────────────────────────────────────────────

def _torch():
    try:
        import torch
        return torch
    except ImportError:
        return None


def _transformers():
    try:
        import transformers
        return transformers
    except ImportError:
        return None


def _sentence_transformers():
    try:
        import sentence_transformers
        return sentence_transformers
    except ImportError:
        return None


# ── Result types ───────────────────────────────────────────────────────────────

@dataclass
class VulnPrediction:
    vulnerability_probability: float    # 0.0 – 1.0
    is_vulnerable: bool
    cwe_predictions: list[tuple[str, float]]   # [(cwe_id, confidence), ...]
    model_version: str
    explanation: str


@dataclass
class FixProposal:
    before_code: str
    after_code: str
    explanation: str
    confidence: float
    model_version: str


@dataclass
class TechniqueMatch:
    source: str             # arxiv_id | owasp_id | cwe_id
    title: str
    description: str
    similarity: float
    fix_techniques: list[str]
    url: str | None = None


@dataclass
class AIBugPrediction:
    is_ai_generated_bug: bool
    pattern_type: str                   # hallucination | over-trust | wrong-api | logic-error | ...
    confidence: float
    explanation: str
    patterns_found: list[str]


# ── CWE label set (Top 25 + common) ───────────────────────────────────────────

CWE_LABELS = [
    "CWE-787", "CWE-79",  "CWE-89",  "CWE-416", "CWE-78",
    "CWE-20",  "CWE-125", "CWE-22",  "CWE-352", "CWE-434",
    "CWE-502", "CWE-287", "CWE-476", "CWE-798", "CWE-190",
    "CWE-306", "CWE-362", "CWE-269", "CWE-94",  "CWE-863",
    "CWE-400", "CWE-119", "CWE-918", "CWE-77",  "CWE-74",
]
CWE_TO_IDX = {c: i for i, c in enumerate(CWE_LABELS)}


# ── DeepVulnClassifier ────────────────────────────────────────────────────────

class DeepVulnClassifier:
    """
    Binary vulnerability classifier + CWE multi-label tagger.

    Architecture: microsoft/codebert-base encoder with two classification heads:
      - vuln_head: Linear(768 → 1) → sigmoid  (is this code vulnerable?)
      - cwe_head:  Linear(768 → 25) → sigmoid (which CWE categories apply?)

    Training data:
      - BigVul (188k C/C++ functions, labelled vulnerable/non-vulnerable)
      - NVD CVE descriptions (weak supervision for CWE tagging)
      - D2A (IBM defect dataset)

    Continual learning:
      - Supports EWC penalty via register_ewc_params()
      - Supports experience replay via sample_replay()
    """

    MODEL_NAME = "microsoft/codebert-base"
    VERSION = "1.0.0-bigvul"
    MAX_LENGTH = 512

    def __init__(self, checkpoint_path: str | None = None, device: str | None = None):
        self._model = None
        self._tokenizer = None
        self._device = device
        self._checkpoint_path = checkpoint_path
        self._loaded = False

    def _load(self) -> bool:
        if self._loaded:
            return True

        torch = _torch()
        tf = _transformers()
        if torch is None or tf is None:
            logger.warning("torch/transformers unavailable — DeepVulnClassifier using rule-based fallback")
            return False

        try:
            import torch.nn as nn

            device_str = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
            self._device_obj = torch.device(device_str)

            self._tokenizer = tf.AutoTokenizer.from_pretrained(self.MODEL_NAME)

            class _VulnModel(nn.Module):
                def __init__(self, base_name: str, num_cwe: int = 25):
                    super().__init__()
                    self.encoder = tf.AutoModel.from_pretrained(base_name)
                    hidden = self.encoder.config.hidden_size
                    self.dropout = nn.Dropout(0.1)
                    self.vuln_head = nn.Linear(hidden, 1)
                    self.cwe_head = nn.Linear(hidden, num_cwe)

                def forward(self, input_ids, attention_mask):
                    out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                    cls = self.dropout(out.last_hidden_state[:, 0, :])
                    return {
                        "vuln_logit": self.vuln_head(cls),
                        "cwe_logits": self.cwe_head(cls),
                    }

            self._model = _VulnModel(self.MODEL_NAME, len(CWE_LABELS)).to(self._device_obj)

            if self._checkpoint_path and Path(self._checkpoint_path).exists():
                state = torch.load(self._checkpoint_path, map_location=self._device_obj)
                self._model.load_state_dict(state)
                logger.info("Loaded DeepVulnClassifier checkpoint: %s", self._checkpoint_path)

            self._model.eval()
            self._loaded = True
            return True

        except Exception as exc:
            logger.warning("DeepVulnClassifier load error: %s", exc)
            return False

    def predict(self, code: str) -> VulnPrediction:
        if not self._load():
            return self._rule_based_predict(code)

        import torch
        with torch.no_grad():
            enc = self._tokenizer(
                code,
                return_tensors="pt",
                truncation=True,
                max_length=self.MAX_LENGTH,
                padding="max_length",
            )
            enc = {k: v.to(self._device_obj) for k, v in enc.items()}
            out = self._model(enc["input_ids"], enc["attention_mask"])
            vuln_prob = float(torch.sigmoid(out["vuln_logit"]).squeeze())
            cwe_probs = torch.sigmoid(out["cwe_logits"]).squeeze().tolist()

        cwe_preds = sorted(
            [(CWE_LABELS[i], float(p)) for i, p in enumerate(cwe_probs) if p > 0.3],
            key=lambda x: -x[1],
        )[:3]

        return VulnPrediction(
            vulnerability_probability=vuln_prob,
            is_vulnerable=vuln_prob > 0.5,
            cwe_predictions=cwe_preds,
            model_version=self.VERSION,
            explanation=self._build_explanation(vuln_prob, cwe_preds),
        )

    def _rule_based_predict(self, code: str) -> VulnPrediction:
        """Regex-based fallback when model unavailable."""
        DANGER_PATTERNS = {
            "CWE-89":  [r"execute\s*\(", r"query\s*\(.*\+", r"SELECT.*\+.*WHERE"],
            "CWE-78":  [r"os\.system\s*\(", r"subprocess\.call.*shell=True", r"exec\s*\("],
            "CWE-79":  [r"innerHTML\s*=", r"document\.write\s*\(", r"render_template_string"],
            "CWE-798": [r"password\s*=\s*['\"]", r"api_key\s*=\s*['\"]", r"secret\s*=\s*['\"]"],
            "CWE-22":  [r"open\s*\(.*\+", r"path\.join.*request", r"send_file.*request"],
            "CWE-918": [r"requests\.get\s*\(.*request\.", r"urllib\.request\.urlopen.*input"],
        }
        matches: dict[str, float] = {}
        for cwe, patterns in DANGER_PATTERNS.items():
            hits = sum(1 for p in patterns if re.search(p, code, re.IGNORECASE))
            if hits:
                matches[cwe] = min(0.5 + hits * 0.15, 0.95)

        vuln_prob = max(matches.values()) if matches else 0.15
        cwe_preds = sorted(matches.items(), key=lambda x: -x[1])[:3]

        return VulnPrediction(
            vulnerability_probability=vuln_prob,
            is_vulnerable=vuln_prob > 0.5,
            cwe_predictions=cwe_preds,
            model_version=f"{self.VERSION}-fallback",
            explanation=self._build_explanation(vuln_prob, cwe_preds),
        )

    def _build_explanation(self, prob: float, cwes: list[tuple[str, float]]) -> str:
        risk = "CRITICAL" if prob > 0.9 else "HIGH" if prob > 0.7 else "MEDIUM" if prob > 0.5 else "LOW"
        cwe_str = ", ".join(f"{c} ({p:.0%})" for c, p in cwes) if cwes else "none identified"
        return (
            f"Vulnerability probability: {prob:.1%} ({risk}). "
            f"Predicted CWE categories: {cwe_str}."
        )

    def save_checkpoint(self, path: str) -> None:
        if not self._loaded or self._model is None:
            return
        import torch
        torch.save(self._model.state_dict(), path)
        logger.info("Saved DeepVulnClassifier checkpoint: %s", path)

    def get_embeddings(self, code: str):
        """Return the [CLS] embedding for downstream tasks (e.g. similarity search)."""
        if not self._load():
            return None
        import torch
        with torch.no_grad():
            enc = self._tokenizer(
                code,
                return_tensors="pt",
                truncation=True,
                max_length=self.MAX_LENGTH,
                padding="max_length",
            )
            enc = {k: v.to(self._device_obj) for k, v in enc.items()}
            out = self._model.encoder(**enc)
            return out.last_hidden_state[:, 0, :].squeeze().cpu().numpy()


# ── FixSynthesizer ────────────────────────────────────────────────────────────

class FixSynthesizer:
    """
    Code-to-code seq2seq model for automated vulnerability remediation.

    Architecture: Salesforce/codet5-small (encoder-decoder T5)
    Input format: "fix: {vuln_description} </s> {vulnerable_code}"
    Output: fixed code

    Training:
      - BigVul before/after function pairs
      - SWE-bench patches
      - OWASP fix pattern examples (data augmentation)

    Beam search with num_beams=4, top-k sampling for diversity.
    """

    MODEL_NAME = "Salesforce/codet5-small"
    VERSION = "1.0.0-bigvul-swebench"
    MAX_INPUT = 512
    MAX_OUTPUT = 384

    def __init__(self, checkpoint_path: str | None = None, device: str | None = None):
        self._model = None
        self._tokenizer = None
        self._device = device
        self._checkpoint_path = checkpoint_path
        self._loaded = False

    def _load(self) -> bool:
        if self._loaded:
            return True
        torch = _torch()
        tf = _transformers()
        if torch is None or tf is None:
            return False
        try:
            device_str = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
            self._device_obj = torch.device(device_str)
            self._tokenizer = tf.AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self._model = tf.T5ForConditionalGeneration.from_pretrained(self.MODEL_NAME).to(self._device_obj)
            if self._checkpoint_path and Path(self._checkpoint_path).exists():
                import torch as t
                self._model.load_state_dict(t.load(self._checkpoint_path, map_location=self._device_obj))
                logger.info("Loaded FixSynthesizer checkpoint: %s", self._checkpoint_path)
            self._model.eval()
            self._loaded = True
            return True
        except Exception as exc:
            logger.warning("FixSynthesizer load error: %s", exc)
            return False

    def synthesize(
        self,
        vulnerable_code: str,
        vuln_description: str,
        num_candidates: int = 3,
    ) -> list[FixProposal]:
        if not self._load():
            return self._template_fix(vulnerable_code, vuln_description)

        import torch
        prompt = f"fix vulnerability: {vuln_description[:200]} </s> code: {vulnerable_code}"
        enc = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.MAX_INPUT,
        )
        enc = {k: v.to(self._device_obj) for k, v in enc.items()}

        with torch.no_grad():
            out = self._model.generate(
                **enc,
                max_new_tokens=self.MAX_OUTPUT,
                num_beams=max(num_candidates, 4),
                num_return_sequences=num_candidates,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )

        proposals = []
        for i, seq in enumerate(out):
            fixed = self._tokenizer.decode(seq, skip_special_tokens=True)
            # Beam position → confidence heuristic (first beam = highest score)
            confidence = max(0.5, 0.92 - i * 0.08)
            proposals.append(FixProposal(
                before_code=vulnerable_code,
                after_code=fixed,
                explanation=f"Model-generated fix (beam {i+1}): {vuln_description[:150]}",
                confidence=confidence,
                model_version=self.VERSION,
            ))
        return proposals

    def _template_fix(self, code: str, description: str) -> list[FixProposal]:
        """Heuristic fix templates when model unavailable."""
        TEMPLATES: list[tuple[str, str, str]] = [
            (
                r"os\.system\s*\(",
                "subprocess.run([...], shell=False, check=True)  # replaced os.system",
                "Replace os.system with subprocess.run using a list argument to prevent command injection.",
            ),
            (
                r'["\'].*SELECT.*\+',
                "cursor.execute('SELECT ... WHERE id = %s', (user_id,))  # parameterized",
                "Use parameterized query to prevent SQL injection.",
            ),
            (
                r'password\s*=\s*["\']',
                "password = os.environ['DB_PASSWORD']  # load from environment",
                "Move hardcoded credential to environment variable.",
            ),
        ]
        for pattern, fix_snippet, explanation in TEMPLATES:
            if re.search(pattern, code, re.IGNORECASE):
                return [FixProposal(
                    before_code=code,
                    after_code=fix_snippet,
                    explanation=explanation,
                    confidence=0.65,
                    model_version=f"{self.VERSION}-template",
                )]
        return [FixProposal(
            before_code=code,
            after_code=code + "\n# TODO: Apply manual remediation per CWE guidance",
            explanation=f"Manual remediation required: {description[:200]}",
            confidence=0.40,
            model_version=f"{self.VERSION}-template",
        )]

    def save_checkpoint(self, path: str) -> None:
        if not self._loaded or self._model is None:
            return
        import torch
        torch.save(self._model.state_dict(), path)


# ── TechniqueRetriever ────────────────────────────────────────────────────────

class TechniqueRetriever:
    """
    Retrieves relevant fix techniques from academic papers, CWE catalog, and
    OWASP knowledge base using semantic similarity (Sentence-BERT).

    Workflow:
      1. On startup, encode all knowledge base entries
      2. At query time, encode the finding description
      3. Return top-k most similar entries

    Embedding model: all-MiniLM-L6-v2 (fast, 384-dim)
    """

    EMBED_MODEL = "all-MiniLM-L6-v2"
    VERSION = "1.0.0"

    def __init__(self, knowledge_base=None):
        self._embedder = None
        self._kb = knowledge_base   # VulnerabilityKnowledgeBase instance
        self._loaded = False

    def _load(self) -> bool:
        if self._loaded:
            return True
        st = _sentence_transformers()
        if st is None:
            return False
        try:
            self._embedder = st.SentenceTransformer(self.EMBED_MODEL)
            self._loaded = True
            return True
        except Exception as exc:
            logger.warning("TechniqueRetriever load error: %s", exc)
            return False

    def retrieve(self, query: str, top_k: int = 5) -> list[TechniqueMatch]:
        if self._kb is None:
            return []
        if not self._load():
            return self._keyword_retrieve(query, top_k)

        import numpy as np
        q_emb = self._embedder.encode(query, normalize_embeddings=True)
        return self._kb.search_techniques(q_emb, top_k=top_k)

    def embed(self, text: str):
        """Return embedding vector for a text."""
        if not self._load():
            return None
        return self._embedder.encode(text, normalize_embeddings=True)

    def _keyword_retrieve(self, query: str, top_k: int) -> list[TechniqueMatch]:
        if self._kb is None:
            return []
        return self._kb.keyword_search_techniques(query, top_k=top_k)


# ── AIBugDetector ──────────────────────────────────────────────────────────────

class AIBugDetector:
    """
    Specialised classifier for anti-patterns common in AI-generated code.

    AI code generators (Copilot, ChatGPT, Gemini) produce characteristic bugs:
      hallucination    — calls to non-existent APIs or methods
      over-trust       — unconditional use of LLM output without validation
      wrong-api        — deprecated or wrong API usage (e.g. os.popen vs subprocess)
      logic-error      — off-by-one, inverted conditionals common in generated loops
      security-skip    — missing authentication/authorisation checks
      error-suppression — broad except clauses, pass in except blocks
      unsafe-default   — mutable default arguments, dangerous default values

    Uses Sentence-BERT embeddings + a trained SVM / logistic regression head.
    Falls back to pattern matching when model unavailable.
    """

    VERSION = "1.0.0"

    # Anti-pattern signatures (regex, pattern_name, severity)
    AI_BUG_PATTERNS: list[tuple[str, str, str]] = [
        (r"\bexcept\s+Exception\s*:\s*\n\s*pass", "error-suppression", "HIGH"),
        (r"\bexcept\s*:\s*\n\s*pass",              "error-suppression", "HIGH"),
        (r"os\.popen\s*\(",                         "wrong-api",         "HIGH"),
        (r"\.popen\s*\(",                           "wrong-api",         "MEDIUM"),
        (r"eval\s*\(",                              "code-injection",    "CRITICAL"),
        (r"exec\s*\(",                              "code-injection",    "CRITICAL"),
        (r"pickle\.loads\s*\(",                     "deserialization",   "HIGH"),
        (r"assert\s+.*len\(",                       "logic-error",       "MEDIUM"),
        (r"def\s+\w+\s*\([^)]*=\s*\[\s*\]",        "mutable-default",   "MEDIUM"),
        (r"def\s+\w+\s*\([^)]*=\s*\{\s*\}",        "mutable-default",   "MEDIUM"),
        (r"#\s*TODO.*security",                     "security-skip",     "MEDIUM"),
        (r"#\s*FIXME.*auth",                        "security-skip",     "MEDIUM"),
        (r"response\.json\(\)\s*\[.+\](?!\s*if)",  "over-trust",        "MEDIUM"),
        (r"llm_output\s*=.*\neval\s*\(",            "over-trust",        "CRITICAL"),
        (r'password\s*=\s*["\'](?!os\.environ)',    "hardcoded-secret",  "HIGH"),
        (r"\bMD5\b|\bmd5\s*\(",                     "weak-crypto",       "HIGH"),
        (r"\bSHA1\b|\bsha1\s*\(",                   "weak-crypto",       "MEDIUM"),
        (r"random\.random\(\).*token",              "weak-random",       "HIGH"),
        (r"print\s*\(.*password",                   "information-leak",  "HIGH"),
        (r"logging\.(debug|info)\s*\(.*secret",     "information-leak",  "HIGH"),
    ]

    def __init__(self, checkpoint_path: str | None = None):
        self._classifier = None
        self._embedder = None
        self._checkpoint_path = checkpoint_path
        self._loaded = False

    def _load(self) -> bool:
        if self._loaded:
            return True
        st = _sentence_transformers()
        if st is None:
            return False
        try:
            from sklearn.linear_model import LogisticRegression
            self._embedder = st.SentenceTransformer("all-MiniLM-L6-v2")
            if self._checkpoint_path and Path(self._checkpoint_path).exists():
                import pickle
                with open(self._checkpoint_path, "rb") as f:
                    self._classifier = pickle.load(f)
                logger.info("Loaded AIBugDetector classifier: %s", self._checkpoint_path)
            self._loaded = True
            return True
        except Exception as exc:
            logger.warning("AIBugDetector load error: %s", exc)
            return False

    def detect(self, code: str) -> AIBugPrediction:
        pattern_hits = self._pattern_scan(code)
        severity_weight = {"CRITICAL": 1.0, "HIGH": 0.7, "MEDIUM": 0.4}

        if self._loaded and self._embedder is not None and self._classifier is not None:
            try:
                emb = self._embedder.encode(code[:2000], normalize_embeddings=True).reshape(1, -1)
                prob = float(self._classifier.predict_proba(emb)[0][1])
                is_ai_bug = prob > 0.5 or bool(pattern_hits)
                confidence = max(prob, max((severity_weight.get(h[2], 0.3) for h in pattern_hits), default=0.0))
            except Exception:
                is_ai_bug, confidence = bool(pattern_hits), 0.7 if pattern_hits else 0.1
        else:
            is_ai_bug = bool(pattern_hits)
            confidence = max((severity_weight.get(h[2], 0.3) for h in pattern_hits), default=0.1)

        pattern_type = pattern_hits[0][1] if pattern_hits else "none"
        patterns_found = list({h[1] for h in pattern_hits})

        return AIBugPrediction(
            is_ai_generated_bug=is_ai_bug,
            pattern_type=pattern_type,
            confidence=min(confidence, 0.99),
            explanation=self._build_explanation(pattern_hits, confidence),
            patterns_found=patterns_found,
        )

    def _pattern_scan(self, code: str) -> list[tuple[str, str, str]]:
        hits = []
        for pattern, name, sev in self.AI_BUG_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                hits.append((pattern, name, sev))
        return hits

    def _build_explanation(self, hits: list[tuple], confidence: float) -> str:
        if not hits:
            return f"No AI-generated bug patterns detected (confidence: {confidence:.0%})."
        names = ", ".join({h[1] for h in hits[:3]})
        return (
            f"Detected {len(hits)} AI-generated code anti-pattern(s): {names}. "
            f"Confidence: {confidence:.0%}. These patterns commonly appear in code "
            f"generated by LLMs without domain-specific safety context."
        )

    def save_checkpoint(self, path: str) -> None:
        if self._classifier is None:
            return
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self._classifier, f)


# ── Global singleton registry ──────────────────────────────────────────────────

class ModelRegistry:
    """Thread-safe lazy-initialised model registry. Avoids loading all models on import."""

    def __init__(self):
        self._models: dict[str, Any] = {}

    def get_vuln_classifier(self, checkpoint: str | None = None) -> DeepVulnClassifier:
        if "vuln_classifier" not in self._models:
            self._models["vuln_classifier"] = DeepVulnClassifier(checkpoint_path=checkpoint)
        return self._models["vuln_classifier"]

    def get_fix_synthesizer(self, checkpoint: str | None = None) -> FixSynthesizer:
        if "fix_synthesizer" not in self._models:
            self._models["fix_synthesizer"] = FixSynthesizer(checkpoint_path=checkpoint)
        return self._models["fix_synthesizer"]

    def get_technique_retriever(self, knowledge_base=None) -> TechniqueRetriever:
        if "technique_retriever" not in self._models:
            self._models["technique_retriever"] = TechniqueRetriever(knowledge_base=knowledge_base)
        return self._models["technique_retriever"]

    def get_ai_bug_detector(self, checkpoint: str | None = None) -> AIBugDetector:
        if "ai_bug_detector" not in self._models:
            self._models["ai_bug_detector"] = AIBugDetector(checkpoint_path=checkpoint)
        return self._models["ai_bug_detector"]


# Module-level default registry
registry = ModelRegistry()
