"""
Base interfaces for all AuditAI test engines and neural assistants.
Every engine must implement BaseEngine; every neural model must implement NeuralAssistant.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class StackInfo:
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    risk_surfaces: List[str] = field(default_factory=list)
    has_contracts: bool = False
    has_tests: bool = False


@dataclass
class EngineContext:
    execution_id: str
    application_id: str
    tenant_id: str
    stack: StackInfo
    source_code: Optional[str] = None
    source_path: Optional[str] = None
    contract_content: Optional[str] = None
    corpus_cases: Optional[List[dict]] = None
    baseline_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FindingData:
    engine: str
    severity: str          # INFO | LOW | MEDIUM | HIGH | CRITICAL
    category: str
    title: str
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    seed: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cwe_id: Optional[str] = None
    neural_score: Optional[float] = None
    pyramid_level: Optional[int] = None


@dataclass
class EngineResult:
    engine: str
    pyramid_level: int
    findings: List[FindingData] = field(default_factory=list)
    score: int = 100
    neural_insights: List[str] = field(default_factory=list)
    summary: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0
    status: str = "COMPLETED"
    error: Optional[str] = None


class NeuralAssistant(ABC):
    """Abstract neural model embedded in each engine."""

    @abstractmethod
    def score(self, context: dict) -> float:
        """Return a probability/confidence score 0.0–1.0."""

    @abstractmethod
    def explain(self, context: dict) -> str:
        """Return a human-readable explanation of the neural assessment."""

    def is_available(self) -> bool:
        """Return False if dependencies (torch, etc.) are not installed."""
        return False


class FallbackNeuralAssistant(NeuralAssistant):
    """Rule-based fallback when neural deps are unavailable."""

    def score(self, context: dict) -> float:
        severity_map = {"CRITICAL": 0.95, "HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.3, "INFO": 0.1}
        return severity_map.get(context.get("severity", "INFO"), 0.5)

    def explain(self, context: dict) -> str:
        return f"Rule-based assessment: severity={context.get('severity')}"

    def is_available(self) -> bool:
        return True


class BaseEngine(ABC):
    name: str = "base"
    version: str = "1.0.0"
    pyramid_level: int = 0
    neural: NeuralAssistant = None

    def __init__(self):
        self.neural = self._init_neural()

    def _init_neural(self) -> NeuralAssistant:
        return FallbackNeuralAssistant()

    @abstractmethod
    def run(self, context: EngineContext) -> EngineResult:
        """Execute tests and return structured findings."""

    def supports(self, stack: StackInfo) -> bool:
        """Return True if engine can handle this stack (override for specificity)."""
        return True
