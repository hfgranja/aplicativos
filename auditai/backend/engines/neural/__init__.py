"""
AuditAI Neural Module — Deep Learning for Vulnerability Detection & Repair
==========================================================================
Connects to real vulnerability databases (NVD/CVE, BigVul, SWE-bench),
academic sources (arXiv, CWE, OWASP) and implements continual learning
so models improve automatically as new bugs and fixes are ingested.

Architecture:
  data_sources   → raw data from CVE/arXiv/BigVul/GitHub/OWASP/SWE-bench
  knowledge_base → embedded vector store (vulnerability + technique + fix)
  models         → DeepVulnClassifier, FixSynthesizer, TechniqueRetriever, AIBugDetector
  continual_learner → EWC + experience replay to prevent catastrophic forgetting
  trainer        → fine-tuning pipeline with evaluation metrics
"""

from .data_sources import (
    NVDConnector,
    ArxivConnector,
    BigVulLoader,
    CWECatalogLoader,
    GitHubAdvisoryLoader,
    SWEBenchLoader,
    OWASPKnowledgeBase,
)
from .knowledge_base import VulnerabilityKnowledgeBase
from .models import (
    DeepVulnClassifier,
    FixSynthesizer,
    TechniqueRetriever,
    AIBugDetector,
)
from .continual_learner import (
    ElasticWeightConsolidation,
    ExperienceReplayBuffer,
    ContinualLearner,
)
from .trainer import ModelTrainer, TrainingConfig, TrainingMetrics

__all__ = [
    # Data sources
    "NVDConnector",
    "ArxivConnector",
    "BigVulLoader",
    "CWECatalogLoader",
    "GitHubAdvisoryLoader",
    "SWEBenchLoader",
    "OWASPKnowledgeBase",
    # Knowledge base
    "VulnerabilityKnowledgeBase",
    # Models
    "DeepVulnClassifier",
    "FixSynthesizer",
    "TechniqueRetriever",
    "AIBugDetector",
    # Continual learning
    "ElasticWeightConsolidation",
    "ExperienceReplayBuffer",
    "ContinualLearner",
    # Training
    "ModelTrainer",
    "TrainingConfig",
    "TrainingMetrics",
]
