"""
Generic SAST rules ported and extended from ai-code-tester/src/analyzers/04_security.js
Covers OWASP Top 10 + CWE catalog patterns for Python, JS/TS, Java, Go.
"""
import re
from typing import List, Tuple

# (pattern, severity, title, description, cwe_id, score_penalty)
GENERIC_RULES: List[Tuple] = [
    # Injection
    (r"eval\s*\(", "CRITICAL", "eval() Usage", "Arbitrary code execution via eval()", "CWE-78", 25),
    (r"exec\s*\(", "CRITICAL", "exec() Usage", "Arbitrary code execution via exec()", "CWE-78", 25),
    (r"subprocess\.call\([^)]*shell\s*=\s*True", "CRITICAL", "Shell Injection",
     "shell=True allows command injection", "CWE-78", 25),
    (r"os\.system\s*\(", "HIGH", "os.system() Usage", "os.system() is vulnerable to injection", "CWE-78", 15),
    # SQL Injection
    (r"execute\s*\(\s*['\"].*%s|execute\s*\(\s*f['\"]|\.format\s*\(.*\)\s*\)", "CRITICAL",
     "SQL Injection Risk", "String formatting in SQL query — use parameterized queries", "CWE-89", 25),
    (r"SELECT\s+\*?\s+FROM.*\+|INSERT\s+INTO.*\+|DELETE\s+FROM.*\+", "CRITICAL",
     "SQL Injection (Concatenation)", "SQL built by string concatenation", "CWE-89", 25),
    # Hardcoded secrets
    (r'(password|passwd|secret|api_key|apikey|token|auth_token)\s*[=:]\s*["\'][^"\']{4,}["\']',
     "CRITICAL", "Hardcoded Secret", "Credential hardcoded in source — use env vars or secrets manager", "CWE-798", 25),
    (r'[A-Z0-9]{20,}', "MEDIUM", "Possible Hardcoded Key",
     "Long uppercase string may be a hardcoded API key", "CWE-798", 5),
    # XSS
    (r'innerHTML\s*=', "HIGH", "XSS via innerHTML", "innerHTML= is vulnerable to XSS", "CWE-79", 15),
    (r'document\.write\s*\(', "HIGH", "XSS via document.write",
     "document.write() is vulnerable to XSS", "CWE-79", 15),
    # Insecure deserialization
    (r'pickle\.loads?\s*\(', "HIGH", "Insecure Deserialization (pickle)",
     "pickle.load() can execute arbitrary code", "CWE-502", 20),
    (r'yaml\.load\s*\([^,)]+\)', "HIGH", "Insecure YAML Load",
     "yaml.load() without Loader is unsafe — use yaml.safe_load()", "CWE-502", 15),
    # Path traversal
    (r'open\s*\(\s*[^)]*\+', "MEDIUM", "Path Traversal Risk",
     "File path constructed from user input may allow directory traversal", "CWE-22", 10),
    # Weak crypto
    (r'\bmd5\b|\bsha1\b', "MEDIUM", "Weak Hash Algorithm",
     "MD5/SHA1 are cryptographically broken — use SHA-256+", "CWE-327", 10),
    (r'random\s*\.\s*random\s*\(\)', "MEDIUM", "Insecure Random",
     "random.random() is not cryptographically secure — use secrets module", "CWE-338", 8),
    # Logging sensitive data
    (r'(log|logger|print)\s*\(.*?(password|token|secret|key|ssn|cpf)', "HIGH",
     "Sensitive Data in Logs", "Credential or PII may be logged", "CWE-532", 15),
    # SSRF
    (r'requests\.(get|post|put|delete)\s*\(\s*[^,)]*\+', "HIGH", "Potential SSRF",
     "URL constructed from user input — validate and whitelist destinations", "CWE-918", 15),
    # Prototype pollution
    (r'\.__proto__\s*=', "CRITICAL", "Prototype Pollution",
     "Direct __proto__ assignment modifies Object prototype", "CWE-1321", 25),
    # Open redirect
    (r'redirect\s*\(\s*[^)]*request\.(args|form|json)', "HIGH", "Open Redirect",
     "Redirect destination from user input — validate before redirect", "CWE-601", 15),
]


def scan_source(code: str, language: str = "generic") -> List[dict]:
    """Run all generic rules against source code. Returns list of finding dicts."""
    findings = []
    lines = code.splitlines()

    for pattern, severity, title, description, cwe_id, penalty in GENERIC_RULES:
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    "severity": severity,
                    "category": "security",
                    "title": title,
                    "description": description,
                    "cwe_id": cwe_id,
                    "line_number": i,
                    "evidence": {"code_snippet": line.strip(), "pattern": pattern},
                    "score_penalty": penalty,
                })

    return findings
