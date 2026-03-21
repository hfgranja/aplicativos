"""
Stack discovery service: detects language, framework, build tools, endpoints, risk surfaces.
"""
import os
import re
from typing import Dict, List, Any


LANGUAGE_INDICATORS = {
    "python": ["requirements.txt", "setup.py", "pyproject.toml", "*.py"],
    "java": ["pom.xml", "build.gradle", "*.java"],
    "go": ["go.mod", "go.sum", "*.go"],
    "typescript": ["tsconfig.json", "*.ts", "*.tsx"],
    "javascript": ["package.json", "*.js", "*.jsx"],
    "dotnet": ["*.csproj", "*.sln", "*.cs"],
    "kotlin": ["*.kt", "build.gradle.kts"],
    "ruby": ["Gemfile", "*.rb"],
    "rust": ["Cargo.toml", "*.rs"],
}

FRAMEWORK_INDICATORS = {
    "fastapi": ["fastapi", "uvicorn"],
    "django": ["django"],
    "flask": ["flask"],
    "spring": ["spring-boot", "springframework"],
    "express": ["express"],
    "nestjs": ["@nestjs"],
    "gin": ["github.com/gin-gonic/gin"],
    "echo": ["github.com/labstack/echo"],
    "react": ["react", "react-dom"],
    "vue": ["vue"],
    "angular": ["@angular"],
}

RISK_PATTERNS = {
    "financial": [r"payment", r"transaction", r"balance", r"credit", r"debit", r"amount", r"currency"],
    "auth": [r"auth", r"login", r"jwt", r"oauth", r"token", r"session", r"password"],
    "pii": [r"cpf", r"cnpj", r"ssn", r"email", r"phone", r"address", r"name"],
    "crypto": [r"encrypt", r"decrypt", r"hash", r"sign", r"certificate", r"tls"],
    "database": [r"query", r"sql", r"orm", r"migration", r"schema"],
    "external_api": [r"http_client", r"requests\.", r"axios", r"fetch("],
}


def discover_stack(source_path: str = None, repo_content: str = None) -> Dict[str, Any]:
    """Analyse a source tree and return a stack_info dict."""
    stack = {
        "languages": [],
        "frameworks": [],
        "build_tools": [],
        "risk_surfaces": [],
        "has_contracts": False,
        "has_tests": False,
        "recommended_engines": [],
        "detected_at": None,
    }

    content = repo_content or ""

    # Language detection
    for lang, indicators in LANGUAGE_INDICATORS.items():
        for indicator in indicators:
            if indicator.replace("*", "") in content.lower():
                if lang not in stack["languages"]:
                    stack["languages"].append(lang)

    # Framework detection
    for fw, keywords in FRAMEWORK_INDICATORS.items():
        for kw in keywords:
            if kw.lower() in content.lower():
                if fw not in stack["frameworks"]:
                    stack["frameworks"].append(fw)

    # Risk surface detection
    for risk_type, patterns in RISK_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, content, re.IGNORECASE):
                if risk_type not in stack["risk_surfaces"]:
                    stack["risk_surfaces"].append(risk_type)
                break

    # Contract detection
    if any(x in content.lower() for x in ["openapi", "swagger", "asyncapi", "graphql", ".proto"]):
        stack["has_contracts"] = True

    # Test detection
    if any(x in content.lower() for x in ["pytest", "unittest", "jest", "mocha", "junit", "testify"]):
        stack["has_tests"] = True

    # Recommend engines based on stack
    stack["recommended_engines"] = _recommend_engines(stack)

    from datetime import datetime
    stack["detected_at"] = datetime.utcnow().isoformat()

    return stack


def _recommend_engines(stack: Dict) -> List[str]:
    engines = ["sast"]  # always

    if stack.get("has_contracts"):
        engines.append("contract")

    if "financial" in stack.get("risk_surfaces", []):
        engines.extend(["property_based", "mutation"])

    if stack.get("has_tests"):
        engines.append("mutation")

    engines.extend(["regression", "fuzzing"])

    if "financial" in stack.get("risk_surfaces", []):
        engines.append("differential")

    engines.extend(["integration", "performance"])

    if "auth" in stack.get("risk_surfaces", []) or "pii" in stack.get("risk_surfaces", []):
        engines.append("chaos")

    # Deduplicate preserving order
    seen = set()
    return [e for e in engines if not (e in seen or seen.add(e))]
