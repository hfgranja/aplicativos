"""
Contract Testing Engine — Level 5 of the testing pyramid.
Validates OpenAPI/AsyncAPI contracts, detects breaking changes,
and uses Sentence-BERT to detect semantic drift.
"""
import time
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData, StackInfo
from engines.contract.parsers.openapi import parse_openapi, validate_openapi, detect_breaking_changes
from engines.contract.neural import ContractNeuralAssistant


class ContractEngine(BaseEngine):
    name = "contract"
    version = "1.0.0"
    pyramid_level = 5

    def _init_neural(self):
        return ContractNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        contract_content = context.contract_content
        if not contract_content:
            return EngineResult(
                engine=self.name, pyramid_level=self.pyramid_level,
                score=100, summary="No contract provided", status="SKIPPED",
            )

        # Parse spec
        spec = parse_openapi(contract_content)
        if not spec:
            return EngineResult(
                engine=self.name, pyramid_level=self.pyramid_level,
                score=0, summary="Failed to parse contract", status="FAILED",
                error="Unable to parse OpenAPI/YAML content",
            )

        # Validate spec completeness
        issues = validate_openapi(spec)
        for issue in issues:
            findings.append(FindingData(
                engine=self.name, pyramid_level=self.pyramid_level,
                severity=issue["severity"],
                category="contract_validation",
                title=issue["title"],
                description=issue["description"],
                neural_score=0.5,
            ))

        # Breaking change detection vs baseline
        baseline_content = context.config.get("baseline_contract")
        if baseline_content:
            old_spec = parse_openapi(baseline_content)
            if old_spec:
                breaking = detect_breaking_changes(old_spec, spec)
                for change in breaking:
                    findings.append(FindingData(
                        engine=self.name, pyramid_level=self.pyramid_level,
                        severity=change["severity"],
                        category="breaking_change",
                        title=change["title"],
                        description=change["description"],
                        neural_score=0.9 if change["severity"] == "CRITICAL" else 0.7,
                    ))

                # Semantic drift analysis on field descriptions
                if self.neural.is_available():
                    old_schemas = _extract_schemas(old_spec)
                    new_schemas = _extract_schemas(spec)
                    drifts = self.neural.detect_field_drift(old_schemas, new_schemas)
                    for drift in drifts:
                        findings.append(FindingData(
                            engine=self.name, pyramid_level=self.pyramid_level,
                            severity="MEDIUM",
                            category="semantic_drift",
                            title=f"Semantic drift: field '{drift['field']}'",
                            description=(
                                f"Field description changed semantically "
                                f"(similarity: {drift['similarity']:.2f}). "
                                f"Old: {drift['old_description'][:100]} | "
                                f"New: {drift['new_description'][:100]}"
                            ),
                            neural_score=1.0 - drift["similarity"],
                        ))

        critical = sum(1 for f in findings if f.severity == "CRITICAL")
        score = max(0, 100 - critical * 25 - len(findings) * 5)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({"description_a": "contract", "description_b": "baseline"}))
        insights.append(f"Validated {len(spec.get('paths', {}))} endpoints, {len(findings)} issue(s) found")

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"{len(findings)} contract issue(s) — {critical} critical",
            execution_time_ms=elapsed_ms,
        )


def _extract_schemas(spec: dict) -> dict:
    """Extract field descriptions from all schemas in the spec."""
    schemas = {}
    components = spec.get("components", {}).get("schemas", {})
    for schema_name, schema in components.items():
        for prop_name, prop in schema.get("properties", {}).items():
            key = f"{schema_name}.{prop_name}"
            schemas[key] = prop
    return schemas
