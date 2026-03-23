"""
AI Test Generator Engine — Level 0 (pre-pyramid).
Analyzes source code and contracts to auto-generate:
  - pytest unit tests
  - Hypothesis property-based tests
  - Synthetic test data cases

Outputs feed the property_based and fuzzing engines via shared context.
"""
import ast
import inspect
import os
import time
from typing import List, Dict, Any, Optional

from engines.base import BaseEngine, EngineContext, EngineResult, StackInfo, FindingData
from engines.ai_test_gen.neural import AITestGenNeural
from engines.ai_test_gen.generators import unit_test_gen, property_gen, synthetic_data_gen


class AITestGenEngine(BaseEngine):
    name = "ai_test_gen"
    version = "1.0.0"
    pyramid_level = 0

    def _init_neural(self):
        return AITestGenNeural()

    def supports(self, stack: StackInfo) -> bool:
        # Works on any Python application with source code
        return "python" in [lang.lower() for lang in stack.languages] or True

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        neural_insights = []

        llm_config = {
            "anthropic_api_key": context.config.get("anthropic_api_key", ""),
            "ollama_url": context.config.get("ollama_url", "http://localhost:11434"),
            "ollama_model": context.config.get("ollama_model", "llama3.2"),
        }

        # Extract functions from source code
        functions = []
        if context.source_code:
            functions = _extract_functions(context.source_code, module_name="<inline>")
        elif context.source_path and os.path.isdir(context.source_path):
            functions = _extract_functions_from_dir(context.source_path)

        total_unit_tests = 0
        total_properties = 0
        total_synthetic = 0
        generated_properties = []
        generated_synthetic_cases = []
        llm_used = False

        if functions:
            # Generate unit tests
            unit_results = unit_test_gen.generate(functions, llm_config)
            for r in unit_results:
                total_unit_tests += len(r.get("tests", []))
                if r.get("source") == "llm":
                    llm_used = True

            # Generate property-based tests
            prop_results = property_gen.generate(functions, llm_config)
            for r in prop_results:
                props = r.get("properties", [])
                generated_properties.extend(props)
                total_properties += len(props)
                if r.get("source") == "llm":
                    llm_used = True

            # Generate synthetic data from contract or inferred schema
            schema = context.config.get("schema", {})
            if not schema and context.contract_content:
                schema = _schema_from_contract(context.contract_content)
            if not schema and functions:
                # Infer schema from the first function with complex args
                schema = _infer_schema_from_functions(functions)

            if schema:
                synthetic_cases = synthetic_data_gen.generate(schema, llm_config, count=15)
                generated_synthetic_cases = synthetic_cases
                total_synthetic = len(synthetic_cases)
                if llm_config.get("anthropic_api_key") or llm_used:
                    llm_used = True

        # Store generated artifacts in context config for downstream engines
        context.config["generated_properties"] = generated_properties
        context.config["generated_synthetic_cases"] = generated_synthetic_cases
        if generated_synthetic_cases:
            # Inject into corpus_cases for fuzzing/property_based engines
            if context.corpus_cases is None:
                context.corpus_cases = []
            context.corpus_cases.extend([
                {"input": c.get("data", {}), "description": c.get("description", "")}
                for c in generated_synthetic_cases
            ])

        # Neural quality score
        neural_ctx = {
            "num_tests": total_unit_tests,
            "num_properties": total_properties,
            "num_synthetic_cases": total_synthetic,
            "llm_generated": llm_used,
        }
        neural_score = self.neural.score(neural_ctx)
        neural_explanation = self.neural.explain(neural_ctx)
        neural_insights.append(neural_explanation)

        # Generate INFO findings summarizing generation results
        if total_unit_tests > 0:
            findings.append(FindingData(
                engine=self.name,
                severity="INFO",
                category="test_generation",
                title=f"Generated {total_unit_tests} unit tests for {len(functions)} function(s)",
                description=(
                    f"AI Test Generator produced {total_unit_tests} pytest unit tests covering "
                    f"{len(functions)} discovered functions. "
                    + ("Generated using LLM (semantic understanding)." if llm_used else "Generated using AST template (configure LLM for higher quality).")
                ),
                evidence={"total_unit_tests": total_unit_tests, "functions_analyzed": len(functions)},
                neural_score=neural_score,
                pyramid_level=0,
            ))

        if total_properties > 0:
            findings.append(FindingData(
                engine=self.name,
                severity="INFO",
                category="test_generation",
                title=f"Generated {total_properties} Hypothesis property test(s)",
                description=(
                    f"Property-based test properties generated for {len(functions)} function(s). "
                    f"These have been injected into the property_based engine's configuration."
                ),
                evidence={"total_properties": total_properties, "properties": generated_properties[:3]},
                neural_score=neural_score,
                pyramid_level=0,
            ))

        if total_synthetic > 0:
            findings.append(FindingData(
                engine=self.name,
                severity="INFO",
                category="test_generation",
                title=f"Generated {total_synthetic} synthetic test data case(s)",
                description=(
                    f"Synthetic test data cases generated and injected into the corpus "
                    f"for use by fuzzing and property_based engines."
                ),
                evidence={"total_cases": total_synthetic, "sample": generated_synthetic_cases[:2]},
                neural_score=neural_score,
                pyramid_level=0,
            ))

        if not functions and not context.source_code and not context.source_path:
            findings.append(FindingData(
                engine=self.name,
                severity="LOW",
                category="test_generation",
                title="No source code available for AI test generation",
                description=(
                    "Supply 'source_code' or 'source_path' in the execution context "
                    "to enable AI-assisted test generation."
                ),
                pyramid_level=0,
            ))

        score = min(100, 60 + total_unit_tests * 2 + total_properties * 3 + total_synthetic)
        summary = (
            f"AI Test Gen: analyzed {len(functions)} function(s), "
            f"generated {total_unit_tests} unit tests, "
            f"{total_properties} properties, "
            f"{total_synthetic} synthetic data cases."
        )

        return EngineResult(
            engine=self.name,
            pyramid_level=self.pyramid_level,
            findings=findings,
            score=min(100, score),
            neural_insights=neural_insights,
            summary=summary,
            evidence={
                "functions_analyzed": len(functions),
                "unit_tests_generated": total_unit_tests,
                "properties_generated": total_properties,
                "synthetic_cases_generated": total_synthetic,
                "llm_used": llm_used,
            },
            execution_time_ms=int((time.time() - start) * 1000),
            status="COMPLETED",
        )


def _extract_functions(source: str, module_name: str = "module") -> List[Dict[str, Any]]:
    """Extract function descriptors from Python source using AST."""
    functions = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return functions

    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private/dunder methods
            if node.name.startswith("_"):
                continue

            args = [a.arg for a in node.args.args if a.arg != "self"]
            arg_types = {}
            for a in node.args.args:
                if a.arg != "self" and a.annotation:
                    try:
                        arg_types[a.arg] = ast.unparse(a.annotation)
                    except Exception:
                        pass

            return_type = "Any"
            if node.returns:
                try:
                    return_type = ast.unparse(node.returns)
                except Exception:
                    pass

            docstring = ast.get_docstring(node) or ""

            # Extract source lines
            func_lines = lines[node.lineno - 1:node.end_lineno]
            func_source = "\n".join(func_lines)

            functions.append({
                "name": node.name,
                "module": module_name,
                "args": args,
                "arg_types": arg_types,
                "return_type": return_type,
                "docstring": docstring,
                "source": func_source[:1500],  # cap source length
                "line_number": node.lineno,
            })
    return functions


def _extract_functions_from_dir(path: str) -> List[Dict[str, Any]]:
    """Extract functions from all .py files in a directory."""
    functions = []
    for root, _, files in os.walk(path):
        for fname in files:
            if fname.endswith(".py") and not fname.startswith("test_"):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        source = f.read()
                    module_name = fname[:-3]
                    functions.extend(_extract_functions(source, module_name))
                except Exception:
                    pass
        if len(functions) >= 50:  # cap at 50 functions total
            break
    return functions[:50]


def _schema_from_contract(contract_content: str) -> Dict[str, Any]:
    """Extract request body schema from an OpenAPI contract."""
    try:
        import json
        spec = json.loads(contract_content)
        # Try to find the first POST endpoint's request body schema
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, op in methods.items():
                if method == "post":
                    body = op.get("requestBody", {})
                    content = body.get("content", {})
                    for media_type, schema_wrapper in content.items():
                        schema = schema_wrapper.get("schema", {})
                        if schema:
                            return schema
    except Exception:
        pass
    return {}


def _infer_schema_from_functions(functions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a basic schema from the most complex function's args."""
    if not functions:
        return {}
    # Pick function with most args
    target = max(functions, key=lambda f: len(f.get("args", [])))
    properties = {}
    for arg, type_hint in target.get("arg_types", {}).items():
        properties[arg] = {"type": type_hint}
    for arg in target.get("args", []):
        if arg not in properties:
            properties[arg] = {"type": "string"}
    return {"properties": properties, "type": "object"}
