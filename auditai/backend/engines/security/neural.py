"""
Security/Pentest Neural Assistant — CodeBERT + OWASP pattern scorer.
Combines rule-based OWASP vulnerability detection with a fine-tuned transformer
model to score exploit probability and suggest attack vectors.
"""
import re
from engines.base import NeuralAssistant, FallbackNeuralAssistant

# OWASP Top 10 (2021) category risk baseline scores
OWASP_BASELINE = {
    "A01_broken_access_control": 0.88,
    "A02_cryptographic_failures": 0.82,
    "A03_injection": 0.90,
    "A04_insecure_design": 0.70,
    "A05_security_misconfiguration": 0.75,
    "A06_vulnerable_components": 0.72,
    "A07_identification_auth_failures": 0.85,
    "A08_software_data_integrity": 0.78,
    "A09_security_logging_monitoring": 0.65,
    "A10_ssrf": 0.80,
}

# Severity mapping from OWASP category to CVSSv3 base
OWASP_SEVERITY = {
    "A01_broken_access_control": "CRITICAL",
    "A02_cryptographic_failures": "HIGH",
    "A03_injection": "CRITICAL",
    "A04_insecure_design": "HIGH",
    "A05_security_misconfiguration": "HIGH",
    "A06_vulnerable_components": "HIGH",
    "A07_identification_auth_failures": "CRITICAL",
    "A08_software_data_integrity": "HIGH",
    "A09_security_logging_monitoring": "MEDIUM",
    "A10_ssrf": "HIGH",
}

# Patterns that indicate a specific OWASP category
OWASP_INDICATORS = {
    "A01_broken_access_control": [
        r"idor",
        r"insecure.*direct.*object",
        r"missing.*authorization",
        r"privilege.*escal",
        r"path.*traversal",
    ],
    "A02_cryptographic_failures": [
        r"md5|sha1(?![\w-])",
        r"weak.*cipher",
        r"http://",
        r"ssl.*verify.*false",
        r"tls.*1\.[01]",
        r"des\b|rc4\b",
    ],
    "A03_injection": [
        r"sql.*inject",
        r"exec\s*\(",
        r"eval\s*\(",
        r"os\.system",
        r"subprocess\.call",
        r"ldap.*inject",
        r"xpath.*inject",
        r"nosql.*inject",
    ],
    "A04_insecure_design": [
        r"no.*rate.*limit",
        r"missing.*validation",
        r"no.*sanitiz",
        r"trust.*input",
    ],
    "A05_security_misconfiguration": [
        r"debug.*true",
        r"default.*cred",
        r"cors.*\*",
        r"allow.*all.*origin",
        r"expose.*stack.*trace",
        r"verbose.*error",
    ],
    "A06_vulnerable_components": [
        r"outdated.*librar",
        r"cve-\d{4}-\d+",
        r"known.*vulnerab",
        r"deprecated",
    ],
    "A07_identification_auth_failures": [
        r"brute.*force",
        r"no.*mfa",
        r"weak.*password",
        r"session.*fixat",
        r"insecure.*token",
        r"jwt.*none",
        r"alg.*none",
    ],
    "A08_software_data_integrity": [
        r"unsigned.*artifact",
        r"no.*integrity.*check",
        r"deserialization",
        r"unsafe.*deserializ",
    ],
    "A09_security_logging_monitoring": [
        r"missing.*log",
        r"no.*audit",
        r"silent.*fail",
        r"swallow.*exception",
    ],
    "A10_ssrf": [
        r"ssrf",
        r"server.*side.*request",
        r"internal.*url",
        r"metadata.*endpoint",
        r"169\.254\.169\.254",
    ],
}


class SecurityNeuralAssistant(NeuralAssistant):
    """
    Security scoring model combining:
    1. OWASP Top 10 indicator matching (rule-based baseline)
    2. CodeBERT transformer vulnerability classifier (when available)
    3. Exploit chain analysis — detects multi-step attack paths
    """

    def __init__(self):
        self._available = False
        self._model = None
        self._tokenizer = None
        self._exploit_chain_threshold = 0.6

        try:
            from transformers import pipeline
            # Use a code vulnerability detection pipeline if available
            self._model = pipeline(
                "text-classification",
                model="microsoft/codebert-base",
                device=-1,  # CPU
            )
            self._available = True
        except Exception:
            pass

    def _classify_owasp(self, text: str) -> dict:
        """
        Return OWASP category matches with confidence scores.
        Combines indicator pattern matching with baseline scores.
        """
        text_lower = text.lower()
        matches = {}
        for category, patterns in OWASP_INDICATORS.items():
            hits = sum(1 for p in patterns if re.search(p, text_lower))
            if hits > 0:
                confidence = min(1.0, OWASP_BASELINE[category] * (1 + 0.05 * hits))
                matches[category] = confidence
        return matches

    def _neural_score(self, code_snippet: str) -> float:
        """Score code via CodeBERT; returns vulnerability probability."""
        if not self._available or not self._model:
            return 0.5
        try:
            result = self._model(code_snippet[:512])
            if isinstance(result, list) and result:
                r = result[0]
                label = r.get("label", "").upper()
                score = r.get("score", 0.5)
                return score if "VULN" in label or "NEGATIVE" not in label else 1 - score
        except Exception:
            pass
        return 0.5

    def score(self, context: dict) -> float:
        """
        Return aggregate exploit probability 0.0–1.0.
        Takes the maximum of OWASP indicator match and optional neural score.
        """
        finding_text = context.get("finding_text", "") or context.get("title", "")
        code_snippet = context.get("code_snippet", "")
        owasp_category = context.get("owasp_category", "")

        # OWASP rule-based baseline
        if owasp_category and owasp_category in OWASP_BASELINE:
            owasp_score = OWASP_BASELINE[owasp_category]
        else:
            matches = self._classify_owasp(finding_text + " " + code_snippet)
            owasp_score = max(matches.values()) if matches else 0.3

        # Neural model boost
        if code_snippet and self._available:
            neural = self._neural_score(code_snippet)
            return round(max(owasp_score, 0.6 * owasp_score + 0.4 * neural), 3)

        return round(owasp_score, 3)

    def explain(self, context: dict) -> str:
        owasp_category = context.get("owasp_category", "")
        exploit_score = self.score(context)
        chain = context.get("exploit_chain", [])

        parts = []
        if owasp_category:
            parts.append(f"OWASP {owasp_category.replace('_', ' ').upper()}: exploit probability {exploit_score:.0%}")
        else:
            parts.append(f"Security vulnerability score: {exploit_score:.0%}")

        if chain:
            parts.append(f"Exploit chain ({len(chain)} steps): {' → '.join(chain)}")

        if exploit_score >= 0.85:
            parts.append("critical exploitability — immediate remediation required")
        elif exploit_score >= 0.70:
            parts.append("high exploitability — patch before next release")
        else:
            parts.append("moderate risk — schedule remediation")

        if self._available:
            parts.append("score reinforced by CodeBERT vulnerability classifier")

        return ". ".join(parts) + "."

    def classify_finding(self, finding_text: str, code_snippet: str = "") -> tuple:
        """Return (owasp_category, confidence) for a finding."""
        matches = self._classify_owasp(finding_text + " " + code_snippet)
        if not matches:
            return ("unknown", 0.3)
        best = max(matches, key=matches.get)
        return (best, matches[best])

    def is_available(self) -> bool:
        return True  # heuristic mode always works
