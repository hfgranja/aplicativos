"""
SAST Engine — Level 1 of the testing pyramid.
Combines rule-based scanning (generic + banking + secrets) with taint analysis
and a CodeBERT neural scorer for each finding.
"""
import time
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData, StackInfo
from engines.sast.rules.generic import scan_source
from engines.sast.rules.banking import scan_banking
from engines.sast.rules.secrets import scan_secrets
from engines.sast.taint import taint_analysis
from engines.sast.neural import SASTNeuralAssistant


class SASTEngine(BaseEngine):
    name = "sast"
    version = "1.0.0"
    pyramid_level = 1

    def _init_neural(self):
        return SASTNeuralAssistant()

    def supports(self, stack: StackInfo) -> bool:
        return True  # SAST runs on all stacks

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        code = context.source_code or ""

        if not code.strip():
            return EngineResult(
                engine=self.name, pyramid_level=self.pyramid_level,
                score=100, summary="No source code provided", status="SKIPPED",
            )

        all_raw_findings = []

        # Rule-based scans
        all_raw_findings.extend(scan_source(code))
        all_raw_findings.extend(scan_secrets(code))
        all_raw_findings.extend(taint_analysis(code))

        # Banking domain rules if relevant
        stack = context.stack
        if "financial" in (stack.risk_surfaces or []):
            all_raw_findings.extend(scan_banking(code))

        # Score each finding with neural model
        findings = []
        total_penalty = 0
        for raw in all_raw_findings:
            neural_score = self.neural.score({
                "code_snippet": raw.get("evidence", {}).get("code_snippet", ""),
                "severity": raw["severity"],
            })
            finding = FindingData(
                engine=self.name,
                pyramid_level=self.pyramid_level,
                severity=raw["severity"],
                category=raw["category"],
                title=raw["title"],
                description=raw["description"],
                evidence=raw.get("evidence", {}),
                line_number=raw.get("line_number"),
                cwe_id=raw.get("cwe_id"),
                neural_score=neural_score,
            )
            findings.append(finding)
            total_penalty += raw.get("score_penalty", 0)

        score = max(0, 100 - total_penalty)
        elapsed_ms = int((time.time() - start) * 1000)

        # Neural insights summary
        insights = []
        if findings:
            high_confidence = [f for f in findings if (f.neural_score or 0) > 0.8]
            if high_confidence:
                insights.append(
                    f"Neural model flagged {len(high_confidence)} finding(s) with >80% vulnerability confidence"
                )
            insights.append(self.neural.explain({"severity": findings[0].severity if findings else "INFO"}))

        return EngineResult(
            engine=self.name,
            pyramid_level=self.pyramid_level,
            findings=findings,
            score=score,
            neural_insights=insights,
            summary=f"Found {len(findings)} issue(s). Score: {score}/100",
            execution_time_ms=elapsed_ms,
        )
