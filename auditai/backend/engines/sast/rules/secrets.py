"""
Secret detection rules — hardcoded credentials, API keys, tokens.
"""
import re
from typing import List

SECRET_PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', "CRITICAL", "AWS Access Key", "CWE-798"),
    (r'(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*[A-Za-z0-9/+=]{40}', "CRITICAL", "AWS Secret Key", "CWE-798"),
    (r'ghp_[A-Za-z0-9]{36}', "CRITICAL", "GitHub Personal Access Token", "CWE-798"),
    (r'ghs_[A-Za-z0-9]{36}', "CRITICAL", "GitHub App Token", "CWE-798"),
    (r'xox[baprs]-[A-Za-z0-9\-]+', "CRITICAL", "Slack Token", "CWE-798"),
    (r'AIza[0-9A-Za-z\-_]{35}', "CRITICAL", "Google API Key", "CWE-798"),
    (r'(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*', "HIGH", "Bearer Token in Code", "CWE-798"),
    (r'(?i)(private[_\-]?key|rsa[_\-]?key)\s*[=:]\s*-----BEGIN', "CRITICAL", "Private Key Embedded", "CWE-321"),
    (r'(?i)db[_\-]?password\s*[=:]\s*["\'][^"\']+["\']', "CRITICAL", "Database Password Hardcoded", "CWE-798"),
    (r'(?i)connection[_\-]?string\s*[=:]\s*["\'].*password=[^"\']+', "CRITICAL", "Connection String with Password", "CWE-798"),
    (r'[A-Za-z0-9+/]{32,}={0,2}', "LOW", "Possible Base64 Encoded Secret", "CWE-798"),
]


def scan_secrets(code: str) -> List[dict]:
    findings = []
    lines = code.splitlines()
    for pattern, severity, title, cwe_id in SECRET_PATTERNS:
        for i, line in enumerate(lines, start=1):
            m = re.search(pattern, line)
            if m:
                # Mask the matched secret value in evidence
                masked = line[:m.start()] + "[REDACTED]" + line[m.end():]
                findings.append({
                    "severity": severity,
                    "category": "secrets",
                    "title": title,
                    "description": f"Potential {title} detected at line {i}",
                    "cwe_id": cwe_id,
                    "line_number": i,
                    "evidence": {"masked_line": masked.strip()},
                    "score_penalty": 25 if severity == "CRITICAL" else 15,
                })
    return findings
