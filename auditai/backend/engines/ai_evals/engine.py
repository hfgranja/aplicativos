"""
AI Evals Engine — Level 11 of the testing pyramid.
Tests applications that embed LLMs or autonomous agents for:
  - Hallucination
  - Prompt injection (OWASP LLM01)
  - RAG quality (retrieval relevance + answer grounding)
  - Bias and toxicity in outputs
"""
import time
from engines.base import BaseEngine, EngineContext, EngineResult, StackInfo
from engines.ai_evals.neural import AIEvalsNeural
from engines.ai_evals.checks import hallucination, prompt_injection, rag_quality, bias_toxicity

# Frameworks that indicate an AI/LLM application
AI_FRAMEWORKS = {
    "langchain", "llamaindex", "llama-index", "openai", "anthropic",
    "huggingface", "transformers", "langflow", "haystack", "semantic-kernel",
    "autogen", "crewai", "langgraph",
}


class AIEvalsEngine(BaseEngine):
    name = "ai_evals"
    version = "1.0.0"
    pyramid_level = 11

    def _init_neural(self):
        return AIEvalsNeural()

    def supports(self, stack: StackInfo) -> bool:
        frameworks_lower = {f.lower() for f in stack.frameworks}
        return bool(frameworks_lower & AI_FRAMEWORKS) or getattr(stack, "has_ai_code", False)

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        all_findings = []

        check_context = {
            "source_code": context.source_code or "",
            "llm_endpoint": context.config.get("llm_endpoint"),
            "llm_outputs": context.config.get("llm_outputs", []),
            "rag_samples": context.config.get("rag_samples", []),
        }

        # Run all four checks
        for check_mod in [hallucination, prompt_injection, rag_quality, bias_toxicity]:
            try:
                findings = check_mod.run(check_context)
                all_findings.extend(findings)
            except Exception as e:
                all_findings.append(__import__("engines.base", fromlist=["FindingData"]).FindingData(
                    engine="ai_evals",
                    severity="LOW",
                    category="ai_evals.check_error",
                    title=f"Check module error: {check_mod.__name__.split('.')[-1]}",
                    description=str(e),
                    pyramid_level=11,
                ))

        # Neural consistency scoring on available outputs
        neural_insights = []
        outputs = check_context.get("llm_outputs", [])
        if outputs and self.neural.is_available():
            scores = []
            for item in outputs[:5]:  # score first 5 outputs to avoid latency
                score = self.neural.score({
                    "reference_context": item.get("context", item.get("prompt", "")),
                    "llm_response": item.get("response", ""),
                })
                scores.append(score)
            if scores:
                avg_score = sum(scores) / len(scores)
                explanation = self.neural.explain({
                    "reference_context": outputs[0].get("context", ""),
                    "llm_response": outputs[0].get("response", ""),
                })
                neural_insights.append(
                    f"Average semantic consistency score: {avg_score:.2f}. {explanation}"
                )
        elif not outputs:
            neural_insights.append(
                "No live LLM outputs provided — running static analysis mode. "
                "Supply 'llm_outputs' or 'llm_endpoint' in execution config for live testing."
            )

        # Score computation
        severity_deductions = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3, "INFO": 0}
        total_deduction = sum(severity_deductions.get(f.severity, 0) for f in all_findings)
        score = max(0, 100 - total_deduction)

        critical_count = sum(1 for f in all_findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in all_findings if f.severity == "HIGH")
        medium_count = sum(1 for f in all_findings if f.severity == "MEDIUM")

        summary = (
            f"AI Evals: {len(all_findings)} finding(s) — "
            f"{critical_count} CRITICAL, {high_count} HIGH, {medium_count} MEDIUM. "
            f"Score: {score}/100."
        )
        if not context.source_code and not check_context.get("llm_outputs") and not check_context.get("llm_endpoint"):
            summary += " (No source code or LLM outputs provided — minimal checks performed.)"

        return EngineResult(
            engine=self.name,
            pyramid_level=self.pyramid_level,
            findings=all_findings,
            score=score,
            neural_insights=neural_insights,
            summary=summary,
            evidence={
                "checks_run": ["hallucination", "prompt_injection", "rag_quality", "bias_toxicity"],
                "static_mode": not bool(check_context.get("llm_outputs") or check_context.get("llm_endpoint")),
                "neural_available": self.neural.is_available(),
            },
            execution_time_ms=int((time.time() - start) * 1000),
            status="COMPLETED",
        )
