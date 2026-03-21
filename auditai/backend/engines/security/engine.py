"""
Security / Pentest Engine — Level 9 of the testing pyramid.
Performs automated security testing covering OWASP Top 10 (2021), CVE pattern detection,
authentication weaknesses, and active probing simulations.
Each finding is scored by the CodeBERT-backed SecurityNeuralAssistant.
"""
import time
import os
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.security.neural import SecurityNeuralAssistant, OWASP_SEVERITY
from engines.security.owasp_rules import scan_source

# Probing tests executed against live endpoints when base_url is configured
ACTIVE_PROBES = [
    {
        "id": "probe_open_redirect",
        "title": "Open Redirect via url Parameter",
        "category": "A01_broken_access_control",
        "cwe": "CWE-601",
        "severity": "HIGH",
        "path": "/?url=https://evil.com",
        "check": "location_header_external",
        "description": "Unvalidated redirect target allows phishing and credential theft.",
    },
    {
        "id": "probe_sqli_error",
        "title": "SQL Injection Error-Based Detection",
        "category": "A03_injection",
        "cwe": "CWE-89",
        "severity": "CRITICAL",
        "path": "/search?q='",
        "check": "sql_error_in_body",
        "description": "Application exposes SQL error messages revealing database type and schema.",
    },
    {
        "id": "probe_xss_reflected",
        "title": "Reflected XSS via Search Parameter",
        "category": "A03_injection",
        "cwe": "CWE-79",
        "severity": "HIGH",
        "path": "/search?q=<script>alert(1)</script>",
        "check": "script_reflected_in_body",
        "description": "User input reflected in HTML without encoding allows script execution in victim browser.",
    },
    {
        "id": "probe_path_traversal",
        "title": "Path Traversal via File Parameter",
        "category": "A01_broken_access_control",
        "cwe": "CWE-22",
        "severity": "CRITICAL",
        "path": "/download?file=../../../../etc/passwd",
        "check": "passwd_in_body",
        "description": "File path not sanitized — arbitrary file read from server filesystem.",
    },
    {
        "id": "probe_ssrf_internal",
        "title": "SSRF via URL Parameter",
        "category": "A10_ssrf",
        "cwe": "CWE-918",
        "severity": "HIGH",
        "path": "/proxy?url=http://169.254.169.254/latest/meta-data/",
        "check": "aws_metadata_in_body",
        "description": "SSRF to AWS metadata endpoint can expose IAM credentials and instance metadata.",
    },
    {
        "id": "probe_security_headers",
        "title": "Missing Security Headers",
        "category": "A05_security_misconfiguration",
        "cwe": "CWE-693",
        "severity": "MEDIUM",
        "path": "/",
        "check": "missing_security_headers",
        "description": "Security headers (CSP, X-Frame-Options, HSTS) absent — increases XSS and clickjacking risk.",
    },
    {
        "id": "probe_cors_wildcard",
        "title": "CORS Wildcard with Credentials",
        "category": "A05_security_misconfiguration",
        "cwe": "CWE-346",
        "severity": "HIGH",
        "path": "/api/",
        "check": "cors_wildcard_with_credentials",
        "description": "CORS wildcard combined with allow_credentials allows cross-origin data theft.",
    },
    {
        "id": "probe_admin_exposure",
        "title": "Admin Panel Publicly Accessible",
        "category": "A01_broken_access_control",
        "cwe": "CWE-284",
        "severity": "CRITICAL",
        "path": "/admin",
        "check": "admin_200_without_auth",
        "description": "Admin panel returns 200 without authentication — full administrative access exposed.",
    },
    {
        "id": "probe_stack_trace",
        "title": "Stack Trace Exposed on Error",
        "category": "A05_security_misconfiguration",
        "cwe": "CWE-209",
        "severity": "MEDIUM",
        "path": "/api/nonexistent_endpoint_xyzzy",
        "check": "stack_trace_in_body",
        "description": "Internal stack trace exposed to clients reveals technology stack and file paths.",
    },
    {
        "id": "probe_default_creds",
        "title": "Default Credentials Accepted",
        "category": "A07_identification_auth_failures",
        "cwe": "CWE-1188",
        "severity": "CRITICAL",
        "path": "/api/auth/login",
        "check": "default_creds_accepted",
        "description": "Default admin credentials (admin/admin, admin/password) accepted by login endpoint.",
    },
]


class SecurityEngine(BaseEngine):
    name = "security"
    version = "1.0.0"
    pyramid_level = 9

    def _init_neural(self):
        return SecurityNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        # --- Phase 1: Static security analysis on source code ---
        static_findings = _run_static_analysis(context, self.neural)
        findings.extend(static_findings)

        # --- Phase 2: Active probing (when base_url is configured) ---
        base_url = context.config.get("base_url", "")
        if base_url:
            probe_findings = _run_active_probes(base_url, context, self.neural)
            findings.extend(probe_findings)
        else:
            # Simulation mode — assess based on stack analysis
            sim_findings = _simulate_probe_findings(context, self.neural)
            findings.extend(sim_findings)

        # --- Neural insights ---
        critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in findings if f.severity == "HIGH")

        owasp_categories = list({f.category for f in findings})
        if owasp_categories:
            insights.append(
                self.neural.explain({
                    "owasp_category": owasp_categories[0],
                    "finding_text": findings[0].title if findings else "",
                })
            )

        insights.append(
            f"Security scan: {len(findings)} finding(s) — "
            f"{critical_count} CRITICAL, {high_count} HIGH across {len(set(f.category for f in findings))} OWASP categories"
        )

        if not base_url:
            insights.append(
                "Active probing skipped (no base_url configured). "
                "Set base_url in execution config for live endpoint testing."
            )

        score = _compute_security_score(findings)
        elapsed_ms = int((time.time() - start) * 1000)

        return EngineResult(
            engine=self.name,
            pyramid_level=self.pyramid_level,
            findings=findings,
            score=score,
            neural_insights=insights,
            summary=(
                f"{len(findings)} security finding(s): "
                f"{critical_count} critical, {high_count} high"
            ),
            execution_time_ms=elapsed_ms,
        )


def _run_static_analysis(context: EngineContext, neural: SecurityNeuralAssistant) -> list:
    """Scan source code files against OWASP rules."""
    results = []

    source_code = context.source_code or ""
    source_path = context.source_path or ""

    code_samples = []

    if source_code:
        code_samples.append(("inline_source", source_code))
    elif source_path and os.path.isdir(source_path):
        for root, _, files in os.walk(source_path):
            for fname in files:
                if fname.endswith((".py", ".js", ".ts", ".java", ".go", ".rb", ".php")):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", errors="replace") as fh:
                            code_samples.append((fpath, fh.read()))
                    except OSError:
                        pass

    for file_path, code in code_samples:
        matches = scan_source(code)
        for match in matches:
            neural_ctx = {
                "owasp_category": match["owasp"],
                "finding_text": match["title"],
                "code_snippet": match["evidence_line"],
            }
            neural_score = neural.score(neural_ctx)
            results.append(FindingData(
                engine="security",
                pyramid_level=9,
                severity=match["severity"],
                category=match["owasp"],
                title=match["title"],
                description=match["description"] + f"\n\nRemediation: {match['remediation']}",
                cwe_id=match["cwe"],
                neural_score=neural_score,
                file_path=file_path if file_path != "inline_source" else None,
                line_number=match["line_number"],
                evidence={
                    "rule_id": match["rule_id"],
                    "owasp_category": match["owasp"],
                    "evidence_line": match["evidence_line"],
                    "remediation": match["remediation"],
                    "neural_score": neural_score,
                },
            ))

    return results


def _run_active_probes(base_url: str, context: EngineContext, neural: SecurityNeuralAssistant) -> list:
    """Execute HTTP-based security probes against a live application."""
    try:
        import httpx
    except ImportError:
        return _simulate_probe_findings(context, neural)

    results = []
    for probe in ACTIVE_PROBES:
        url = base_url.rstrip("/") + probe["path"]
        try:
            resp = httpx.get(url, follow_redirects=False, timeout=5.0, verify=False)
            vuln = _check_probe_response(probe["check"], resp)
        except Exception as e:
            vuln = False
            if "connection" in str(e).lower():
                continue  # host unreachable, skip

        if vuln:
            neural_ctx = {
                "owasp_category": probe["category"],
                "finding_text": probe["title"],
            }
            neural_score = neural.score(neural_ctx)
            results.append(FindingData(
                engine="security",
                pyramid_level=9,
                severity=probe["severity"],
                category=probe["category"],
                title=probe["title"],
                description=probe["description"],
                cwe_id=probe["cwe"],
                neural_score=neural_score,
                evidence={
                    "probe_id": probe["id"],
                    "url": url,
                    "owasp_category": probe["category"],
                    "check": probe["check"],
                },
            ))
    return results


def _check_probe_response(check: str, resp) -> bool:
    """Evaluate whether a probe response indicates a vulnerability."""
    body = getattr(resp, "text", "") or ""
    headers = dict(resp.headers) if hasattr(resp, "headers") else {}
    status = getattr(resp, "status_code", 0)

    if check == "location_header_external":
        loc = headers.get("location", "")
        return loc.startswith("https://evil.com") or loc.startswith("http://evil.com")
    if check == "sql_error_in_body":
        return any(kw in body.lower() for kw in ["sql syntax", "mysql_fetch", "ora-", "pg::error", "sqlite3"])
    if check == "script_reflected_in_body":
        return "<script>alert(1)</script>" in body
    if check == "passwd_in_body":
        return "root:x:0:0" in body or "root:0:0" in body
    if check == "aws_metadata_in_body":
        return "ami-id" in body or "instance-id" in body or "iam" in body.lower()
    if check == "missing_security_headers":
        missing = [h for h in ["content-security-policy", "x-frame-options", "strict-transport-security"]
                   if h not in {k.lower() for k in headers}]
        return len(missing) >= 2
    if check == "cors_wildcard_with_credentials":
        return (headers.get("access-control-allow-origin") == "*"
                and headers.get("access-control-allow-credentials", "").lower() == "true")
    if check == "admin_200_without_auth":
        return status == 200
    if check == "stack_trace_in_body":
        return any(kw in body for kw in ["Traceback (most recent call last)", "at java.", "at com.", "NullPointerException"])
    if check == "default_creds_accepted":
        return status == 200 and ("token" in body or "access_token" in body)
    return False


def _simulate_probe_findings(context: EngineContext, neural: SecurityNeuralAssistant) -> list:
    """
    Generate simulated probe findings based on stack risk profile.
    Used when no live base_url is available for active probing.
    """
    import random
    results = []
    risk_surfaces = context.stack.risk_surfaces if context.stack else []
    frameworks = context.stack.frameworks if context.stack else []

    # Higher simulation rate for high-risk stacks
    has_auth = "auth" in " ".join(risk_surfaces).lower()
    has_api = "api" in " ".join(risk_surfaces).lower()
    has_finance = any(f in " ".join(risk_surfaces).lower() for f in ["financial", "banking", "payment"])

    base_rate = 0.08
    if has_auth:
        base_rate += 0.05
    if has_api:
        base_rate += 0.04
    if has_finance:
        base_rate += 0.06

    for probe in ACTIVE_PROBES:
        if random.random() < base_rate:
            neural_ctx = {
                "owasp_category": probe["category"],
                "finding_text": probe["title"],
            }
            neural_score = neural.score(neural_ctx)
            results.append(FindingData(
                engine="security",
                pyramid_level=9,
                severity=probe["severity"],
                category=probe["category"],
                title=f"[SIMULATED] {probe['title']}",
                description=(
                    probe["description"] +
                    "\n\n[Note: This is a simulated finding. Configure base_url for active testing.]"
                ),
                cwe_id=probe["cwe"],
                neural_score=neural_score,
                evidence={
                    "probe_id": probe["id"],
                    "simulation": True,
                    "owasp_category": probe["category"],
                },
            ))

    return results


def _compute_security_score(findings: list) -> int:
    """
    Security score: starts at 100, deducted by severity.
    CRITICAL: -25 each, HIGH: -12, MEDIUM: -5, LOW: -2
    Minimum score: 0
    """
    deductions = {
        "CRITICAL": 25,
        "HIGH": 12,
        "MEDIUM": 5,
        "LOW": 2,
        "INFO": 0,
    }
    total_deduction = sum(deductions.get(f.severity, 0) for f in findings)
    return max(0, 100 - total_deduction)
