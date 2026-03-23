"""
OpenAPI / Swagger contract parser and validator.
Ported and extended from ai-code-tester/src/analyzers/12_apiContracts.js
"""
import json
import re
from typing import Dict, List, Any, Optional


def parse_openapi(content: str) -> Optional[dict]:
    """Parse JSON or YAML OpenAPI spec."""
    content = content.strip()
    if content.startswith("{"):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
    try:
        import yaml
        return yaml.safe_load(content)
    except Exception:
        return None


def validate_openapi(spec: dict) -> List[dict]:
    """Validate an OpenAPI spec for completeness and correctness."""
    issues = []

    if "openapi" not in spec and "swagger" not in spec:
        issues.append({"severity": "HIGH", "title": "Missing OpenAPI version",
                        "description": "Spec must include 'openapi' or 'swagger' version field"})

    if "info" not in spec:
        issues.append({"severity": "MEDIUM", "title": "Missing info block", "description": "info is required"})

    paths = spec.get("paths", {})
    if not paths:
        issues.append({"severity": "LOW", "title": "No paths defined", "description": "API has no endpoints"})

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            if "responses" not in operation:
                issues.append({
                    "severity": "HIGH",
                    "title": f"Missing responses: {method.upper()} {path}",
                    "description": "Every operation must define responses",
                })
            responses = operation.get("responses", {})
            if "200" not in responses and "201" not in responses and "204" not in responses:
                issues.append({
                    "severity": "MEDIUM",
                    "title": f"No success response: {method.upper()} {path}",
                    "description": "Operation should define a 2xx response",
                })
            if method in ("post", "put", "patch") and "requestBody" not in operation:
                issues.append({
                    "severity": "MEDIUM",
                    "title": f"Missing requestBody: {method.upper()} {path}",
                    "description": "Mutating operations should document request body",
                })

    return issues


def detect_breaking_changes(old_spec: dict, new_spec: dict) -> List[dict]:
    """Detect breaking changes between two OpenAPI spec versions."""
    changes = []
    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    # Removed paths
    for path in old_paths:
        if path not in new_paths:
            changes.append({
                "severity": "CRITICAL",
                "title": f"Endpoint removed: {path}",
                "description": "Removing an endpoint is a breaking change",
            })

    # Removed methods
    for path in old_paths:
        if path in new_paths:
            for method in old_paths[path]:
                if method not in new_paths[path]:
                    changes.append({
                        "severity": "CRITICAL",
                        "title": f"Method removed: {method.upper()} {path}",
                        "description": "Removing an HTTP method is a breaking change",
                    })

    # Required parameter added
    for path in new_paths:
        if path in old_paths:
            for method in new_paths[path]:
                if method in old_paths[path]:
                    old_params = {p["name"]: p for p in old_paths[path][method].get("parameters", [])}
                    new_params = {p["name"]: p for p in new_paths[path][method].get("parameters", [])}
                    for name, param in new_params.items():
                        if name not in old_params and param.get("required"):
                            changes.append({
                                "severity": "HIGH",
                                "title": f"New required parameter: {name} on {method.upper()} {path}",
                                "description": "Adding a required parameter breaks existing clients",
                            })

    return changes
