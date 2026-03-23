"""
Neural Model API
================
REST endpoints for the AuditAI deep learning module:

  GET  /neural/status          — model load status + knowledge base stats
  POST /neural/train           — trigger async training run (background task)
  POST /neural/ingest          — ingest a specific data source into the KB
  GET  /neural/search          — semantic search over the knowledge base
  POST /neural/predict         — run vulnerability classifier on a code snippet
  POST /neural/synthesize-fix  — run fix synthesizer on a before-code snippet
  GET  /neural/training-jobs   — list training job history
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, get_current_admin
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/neural", tags=["neural"])

# ---------------------------------------------------------------------------
# In-memory job registry (replaced by Celery in production)
# ---------------------------------------------------------------------------

_training_jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class TrainingRequest(BaseModel):
    use_bigvul: bool = True
    use_swebench: bool = True
    use_nvd: bool = True
    use_arxiv: bool = True
    nvd_keyword: str = "injection"
    arxiv_query: str = "vulnerability detection deep learning"
    epochs: int = Field(default=2, ge=1, le=10)
    batch_size: int = Field(default=16, ge=4, le=64)
    learning_rate: float = Field(default=2e-5, ge=1e-6, le=1e-3)
    max_vuln_samples: int = Field(default=2000, ge=100, le=50000)
    max_fix_samples: int = Field(default=500, ge=50, le=10000)


class IngestRequest(BaseModel):
    source: str = Field(
        description="One of: nvd, arxiv, cwe, owasp, github",
        pattern="^(nvd|arxiv|cwe|owasp|github)$",
    )
    keyword: str = "injection"
    max_results: int = Field(default=100, ge=1, le=1000)


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=5, ge=1, le=50)
    source_filter: str | None = None   # nvd | cwe | arxiv | owasp | fix_pattern


class PredictRequest(BaseModel):
    code: str = Field(min_length=5, max_length=20000)
    language: str = "python"


class SynthesizeRequest(BaseModel):
    before_code: str = Field(min_length=5, max_length=10000)
    vuln_description: str = ""
    language: str = "python"


# ---------------------------------------------------------------------------
# Lazy singletons for KB + models
# ---------------------------------------------------------------------------

_kb = None
_learner = None


def _get_kb():
    global _kb
    if _kb is None:
        try:
            from engines.neural.knowledge_base import VulnerabilityKnowledgeBase
            _kb = VulnerabilityKnowledgeBase(persist_path="./data/vuln_kb")
        except Exception as exc:
            logger.warning("Could not initialise knowledge base: %s", exc)
    return _kb


def _get_learner():
    global _learner
    if _learner is None:
        try:
            from engines.neural.continual_learner import ContinualLearner
            _learner = ContinualLearner(checkpoint_dir="./data/checkpoints")
        except Exception as exc:
            logger.warning("Could not initialise continual learner: %s", exc)
    return _learner


# ---------------------------------------------------------------------------
# GET /neural/status
# ---------------------------------------------------------------------------

@router.get("/status")
async def neural_status(current_user: User = Depends(get_current_user)):
    """Return model availability, knowledge base stats, and training job count."""
    status: dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "models": {},
        "knowledge_base": {},
        "training_jobs": {
            "total": len(_training_jobs),
            "running": sum(1 for j in _training_jobs.values() if j["status"] == "running"),
            "completed": sum(1 for j in _training_jobs.values() if j["status"] == "completed"),
            "failed": sum(1 for j in _training_jobs.values() if j["status"] == "failed"),
        },
    }

    # Model availability
    try:
        import torch
        status["models"]["torch_available"] = True
        status["models"]["cuda_available"] = torch.cuda.is_available()
    except ImportError:
        status["models"]["torch_available"] = False
        status["models"]["cuda_available"] = False

    try:
        import transformers  # noqa: F401
        status["models"]["transformers_available"] = True
    except ImportError:
        status["models"]["transformers_available"] = False

    try:
        import sentence_transformers  # noqa: F401
        status["models"]["sentence_transformers_available"] = True
    except ImportError:
        status["models"]["sentence_transformers_available"] = False

    # Check if models are loaded
    try:
        from engines.neural.models import ModelRegistry
        registry = ModelRegistry.get_instance()
        status["models"]["classifier_loaded"] = registry.get_classifier()._loaded
        status["models"]["synthesizer_loaded"] = registry.get_synthesizer()._loaded
        status["models"]["retriever_loaded"] = registry.get_retriever()._loaded
    except Exception as exc:
        status["models"]["load_error"] = str(exc)

    # Knowledge base stats
    kb = _get_kb()
    if kb is not None:
        try:
            status["knowledge_base"] = kb.stats()
        except Exception as exc:
            status["knowledge_base"]["error"] = str(exc)
    else:
        status["knowledge_base"]["available"] = False

    return status


# ---------------------------------------------------------------------------
# POST /neural/train
# ---------------------------------------------------------------------------

@router.post("/train")
async def start_training(
    req: TrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin),
):
    """
    Launch a background training run (admin only).
    Returns a job_id that can be polled via GET /neural/training-jobs/{job_id}.
    """
    job_id = str(uuid.uuid4())
    _training_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": None,
        "metrics": [],
        "error": None,
        "triggered_by": current_user.email,
    }

    background_tasks.add_task(_run_training_job, job_id, req)
    return {"job_id": job_id, "status": "queued"}


async def _run_training_job(job_id: str, req: TrainingRequest) -> None:
    job = _training_jobs[job_id]
    job["status"] = "running"
    try:
        from engines.neural.trainer import ModelTrainer, TrainingConfig
        from engines.neural.data_sources import (
            BigVulLoader, SWEBenchLoader, NVDConnector, ArxivConnector,
        )

        config = TrainingConfig(
            use_bigvul=req.use_bigvul,
            use_swebench=req.use_swebench,
            use_nvd=req.use_nvd,
            use_arxiv=req.use_arxiv,
            nvd_keyword=req.nvd_keyword,
            arxiv_query=req.arxiv_query,
            epochs=req.epochs,
            batch_size=req.batch_size,
            learning_rate=req.learning_rate,
            max_vuln_samples=req.max_vuln_samples,
            max_fix_samples=req.max_fix_samples,
        )

        kb = _get_kb()
        learner = _get_learner()
        trainer = ModelTrainer(config=config, kb=kb, learner=learner)

        bigvul = BigVulLoader() if req.use_bigvul else None
        swb = SWEBenchLoader() if req.use_swebench else None
        nvd = NVDConnector() if req.use_nvd else None
        arxiv = ArxivConnector() if req.use_arxiv else None

        metrics_list = await trainer.train_from_sources(
            bigvul_loader=bigvul,
            swb_loader=swb,
            nvd_connector=nvd,
            arxiv_connector=arxiv,
        )

        job["metrics"] = [m.summary() for m in metrics_list]
        job["status"] = "completed"
        job["finished_at"] = datetime.utcnow().isoformat()
        logger.info("Training job %s completed: %d models trained", job_id, len(metrics_list))

    except Exception as exc:
        logger.error("Training job %s failed: %s", job_id, exc, exc_info=True)
        job["status"] = "failed"
        job["error"] = str(exc)
        job["finished_at"] = datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# GET /neural/training-jobs
# ---------------------------------------------------------------------------

@router.get("/training-jobs")
async def list_training_jobs(current_user: User = Depends(get_current_admin)):
    return {"jobs": list(_training_jobs.values())}


@router.get("/training-jobs/{job_id}")
async def get_training_job(job_id: str, current_user: User = Depends(get_current_admin)):
    job = _training_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ---------------------------------------------------------------------------
# POST /neural/ingest
# ---------------------------------------------------------------------------

@router.post("/ingest")
async def ingest_source(
    req: IngestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin),
):
    """Ingest a specific data source into the knowledge base (admin only)."""
    job_id = str(uuid.uuid4())
    _training_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "type": "ingest",
        "source": req.source,
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": None,
        "added": 0,
        "error": None,
    }
    background_tasks.add_task(_run_ingest_job, job_id, req)
    return {"job_id": job_id, "status": "queued", "source": req.source}


async def _run_ingest_job(job_id: str, req: IngestRequest) -> None:
    job = _training_jobs[job_id]
    job["status"] = "running"
    try:
        kb = _get_kb()
        if kb is None:
            raise RuntimeError("Knowledge base unavailable")

        added = 0
        if req.source == "nvd":
            from engines.neural.data_sources import NVDConnector
            connector = NVDConnector()
            added = await kb.ingest_nvd(connector, keyword=req.keyword, max_results=req.max_results)

        elif req.source == "arxiv":
            from engines.neural.data_sources import ArxivConnector
            connector = ArxivConnector()
            added = await kb.ingest_arxiv(connector, query=req.keyword, max_results=req.max_results)

        elif req.source == "cwe":
            from engines.neural.data_sources import CWECatalogLoader
            loader = CWECatalogLoader()
            added = kb.ingest_cwe(loader)

        elif req.source == "owasp":
            from engines.neural.data_sources import OWASPKnowledgeBase
            owasp_kb = OWASPKnowledgeBase()
            added = kb.ingest_owasp(owasp_kb)

        elif req.source == "github":
            from engines.neural.data_sources import GitHubAdvisoryLoader
            loader = GitHubAdvisoryLoader()
            records = await loader.search(keyword=req.keyword, max_results=req.max_results)
            from engines.neural.knowledge_base import KBEntry
            for rec in records:
                entry = KBEntry(
                    entry_id=f"ghsa:{rec.cve_id}",
                    source="ghsa",
                    entry_type="vulnerability",
                    title=rec.cve_id,
                    description=rec.description,
                    metadata={
                        "cve_id": rec.cve_id,
                        "severity": rec.severity,
                        "cvss_score": rec.cvss_score,
                        "cwe_ids": rec.cwe_ids,
                        "published": rec.published,
                        "references": rec.references[:3],
                    },
                )
                if not kb._duplicate(entry.entry_id):
                    kb.add_entry(entry)
                    added += 1

        kb.save()
        job["added"] = added
        job["status"] = "completed"
        job["finished_at"] = datetime.utcnow().isoformat()
        logger.info("Ingest job %s: added %d entries from %s", job_id, added, req.source)

    except Exception as exc:
        logger.error("Ingest job %s failed: %s", job_id, exc, exc_info=True)
        job["status"] = "failed"
        job["error"] = str(exc)
        job["finished_at"] = datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# GET /neural/search
# ---------------------------------------------------------------------------

@router.get("/search")
async def search_knowledge_base(
    q: str = Query(min_length=2, max_length=500, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=50),
    source: str | None = Query(default=None, description="Filter by source (nvd, cwe, arxiv, owasp)"),
    current_user: User = Depends(get_current_user),
):
    """Semantic search over the vulnerability knowledge base."""
    kb = _get_kb()
    if kb is None or len(kb) == 0:
        return {"query": q, "results": [], "total_entries": 0}

    raw = kb.search(q, top_k=top_k * 3 if source else top_k)  # over-fetch if filtering

    results = []
    for entry, score in raw:
        if source and entry.source != source:
            continue
        results.append({
            "entry_id": entry.entry_id,
            "source": entry.source,
            "entry_type": entry.entry_type,
            "title": entry.title,
            "description": entry.description[:300],
            "similarity": round(score, 4),
            "metadata": {
                k: v for k, v in entry.metadata.items()
                if k not in ("before_code", "after_code")  # omit large fields
            },
        })
        if len(results) >= top_k:
            break

    return {
        "query": q,
        "results": results,
        "total_kb_entries": len(kb),
    }


# ---------------------------------------------------------------------------
# POST /neural/predict
# ---------------------------------------------------------------------------

@router.post("/predict")
async def predict_vulnerability(
    req: PredictRequest,
    current_user: User = Depends(get_current_user),
):
    """Run the DeepVulnClassifier on a code snippet."""
    try:
        from engines.neural.models import ModelRegistry
        classifier = ModelRegistry.get_instance().get_classifier()
        pred = classifier.predict(req.code)
        return {
            "is_vulnerable": pred.is_vulnerable,
            "confidence": round(pred.confidence, 4),
            "cwe_predictions": pred.cwe_predictions,
            "severity": pred.severity,
            "explanation": pred.explanation,
        }
    except Exception as exc:
        logger.error("Prediction error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")


# ---------------------------------------------------------------------------
# POST /neural/synthesize-fix
# ---------------------------------------------------------------------------

@router.post("/synthesize-fix")
async def synthesize_fix(
    req: SynthesizeRequest,
    current_user: User = Depends(get_current_user),
):
    """Run the FixSynthesizer to generate a patched version of vulnerable code."""
    try:
        from engines.neural.models import ModelRegistry
        synthesizer = ModelRegistry.get_instance().get_synthesizer()
        result = synthesizer.synthesize(req.before_code, req.vuln_description)
        return {
            "fixed_code": result.fixed_code,
            "diff": result.diff,
            "explanation": result.explanation,
            "confidence": round(result.confidence, 4),
            "method": result.method,
        }
    except Exception as exc:
        logger.error("Fix synthesis error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {exc}")


# ---------------------------------------------------------------------------
# POST /neural/online-learn  (accept feedback on a finding)
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    code: str = Field(min_length=5, max_length=20000)
    is_vulnerable: bool
    cwe_id: str | None = None
    fix_before: str | None = None
    fix_after: str | None = None


@router.post("/online-learn")
async def online_learn(
    req: FeedbackRequest,
    current_user: User = Depends(get_current_admin),
):
    """
    Incorporate human feedback into the continual learner (admin only).
    This updates the replay buffer and triggers an EWC-regularised micro-step.
    """
    try:
        from engines.neural.trainer import ModelTrainer, TrainingConfig
        config = TrainingConfig(epochs=1, batch_size=1, max_vuln_samples=1)
        kb = _get_kb()
        learner = _get_learner()
        trainer = ModelTrainer(config=config, kb=kb, learner=learner)
        await trainer.train_on_finding(
            code=req.code,
            label=int(req.is_vulnerable),
            fix_before=req.fix_before,
            fix_after=req.fix_after,
            cwe_id=req.cwe_id,
        )
        return {"status": "ok", "message": "Feedback incorporated into continual learner"}
    except Exception as exc:
        logger.error("Online learning error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Online learning failed: {exc}")
