"""
OWASP Top 10 (2021) security rules for the Security/Pentest engine.
Each rule defines the detection pattern, category, severity, CWE, and remediation guidance.
"""
from typing import List, Dict, Any
import re

OWASP_RULES: List[Dict[str, Any]] = [
    # A01 — Broken Access Control
    {
        "id": "SEC-A01-001",
        "owasp": "A01_broken_access_control",
        "title": "Insecure Direct Object Reference (IDOR)",
        "pattern": r"(user_?id|account_?id|doc_?id)\s*=\s*request\.(GET|POST|args|form|data|json)",
        "severity": "CRITICAL",
        "cwe": "CWE-639",
        "description": "Object ID read directly from request without authorization check. Attacker can enumerate/access other users' data.",
        "remediation": "Validate that the authenticated user has permission to access the requested resource before returning data.",
    },
    {
        "id": "SEC-A01-002",
        "owasp": "A01_broken_access_control",
        "title": "Path Traversal via User Input",
        "pattern": r"(open|read|write|include|require)\s*\(\s*.*\+\s*(request|params|args|user_input)",
        "severity": "CRITICAL",
        "cwe": "CWE-22",
        "description": "File path constructed from user-controlled input without sanitization.",
        "remediation": "Use allowlists for valid file paths and reject any input containing '..' or absolute path characters.",
    },
    {
        "id": "SEC-A01-003",
        "owasp": "A01_broken_access_control",
        "title": "Missing Function-Level Authorization",
        "pattern": r"@(app|router)\.(delete|put|patch)\s*\([^)]*\)\s*\ndef\s+\w+\s*\([^)]*\):\s*(?!.*require_permission|.*@require|.*authorize|.*permission_required)",
        "severity": "HIGH",
        "cwe": "CWE-285",
        "description": "State-changing HTTP endpoint (DELETE/PUT/PATCH) without authorization decorator.",
        "remediation": "Apply authorization decorators or middleware to all state-changing endpoints.",
    },
    # A02 — Cryptographic Failures
    {
        "id": "SEC-A02-001",
        "owasp": "A02_cryptographic_failures",
        "title": "Weak Hashing Algorithm (MD5/SHA1)",
        "pattern": r"hashlib\.(md5|sha1)\s*\(",
        "severity": "HIGH",
        "cwe": "CWE-327",
        "description": "MD5 and SHA1 are cryptographically broken and must not be used for security-sensitive operations.",
        "remediation": "Replace with SHA-256 or bcrypt/argon2 for password hashing.",
    },
    {
        "id": "SEC-A02-002",
        "owasp": "A02_cryptographic_failures",
        "title": "Hardcoded Encryption Key",
        "pattern": r"(key|secret|iv|salt)\s*=\s*['\"][a-zA-Z0-9+/=]{8,}['\"]",
        "severity": "CRITICAL",
        "cwe": "CWE-321",
        "description": "Encryption key hardcoded in source code. Any developer with repo access can decrypt sensitive data.",
        "remediation": "Load keys from environment variables or a secrets manager (Vault, AWS Secrets Manager).",
    },
    {
        "id": "SEC-A02-003",
        "owasp": "A02_cryptographic_failures",
        "title": "TLS Certificate Verification Disabled",
        "pattern": r"(verify\s*=\s*False|ssl_verify\s*=\s*False|CERT_NONE|check_hostname\s*=\s*False)",
        "severity": "HIGH",
        "cwe": "CWE-295",
        "description": "TLS certificate verification disabled — vulnerable to man-in-the-middle attacks.",
        "remediation": "Always verify TLS certificates in production. Use verify=True and proper CA bundles.",
    },
    # A03 — Injection
    {
        "id": "SEC-A03-001",
        "owasp": "A03_injection",
        "title": "SQL Injection via String Concatenation",
        "pattern": r'(execute|query|cursor\.execute)\s*\(\s*["\'].*(%s|["\'] *\+|\.format|f")',
        "severity": "CRITICAL",
        "cwe": "CWE-89",
        "description": "SQL query constructed by string concatenation or format with user input. Allows full database compromise.",
        "remediation": "Use parameterized queries or ORM query builders exclusively. Never concatenate user input into SQL.",
    },
    {
        "id": "SEC-A03-002",
        "owasp": "A03_injection",
        "title": "OS Command Injection",
        "pattern": r"(os\.system|subprocess\.(call|run|Popen|check_output))\s*\([^)]*\+",
        "severity": "CRITICAL",
        "cwe": "CWE-78",
        "description": "OS command constructed from string concatenation with potentially user-controlled input.",
        "remediation": "Use subprocess with list arguments and avoid shell=True. Validate and allowlist all command parameters.",
    },
    {
        "id": "SEC-A03-003",
        "owasp": "A03_injection",
        "title": "LDAP Injection Risk",
        "pattern": r"ldap.*search.*\+|ldap.*filter.*format",
        "severity": "HIGH",
        "cwe": "CWE-90",
        "description": "LDAP query constructed by string concatenation may allow LDAP injection.",
        "remediation": "Escape all user input in LDAP queries using proper escaping functions.",
    },
    # A05 — Security Misconfiguration
    {
        "id": "SEC-A05-001",
        "owasp": "A05_security_misconfiguration",
        "title": "Debug Mode Enabled",
        "pattern": r"(DEBUG\s*=\s*True|debug\s*=\s*True|app\.run\s*\([^)]*debug\s*=\s*True)",
        "severity": "HIGH",
        "cwe": "CWE-215",
        "description": "Debug mode exposes stack traces, environment variables, and interactive debugger to all users.",
        "remediation": "Set DEBUG=False in production. Use environment variables to control debug mode.",
    },
    {
        "id": "SEC-A05-002",
        "owasp": "A05_security_misconfiguration",
        "title": "Wildcard CORS Origin",
        "pattern": r"(Access-Control-Allow-Origin['\"]?\s*:\s*['\"]?\*|allow_origins\s*=\s*\[['\\"]\*['\\"]\]|CORSMiddleware[^)]*allow_origins.*\*)",
        "severity": "HIGH",
        "cwe": "CWE-346",
        "description": "CORS policy allows any origin. Combined with cookies this enables cross-site data theft.",
        "remediation": "Specify explicit allowed origins instead of wildcards. Never use '*' with allow_credentials=True.",
    },
    {
        "id": "SEC-A05-003",
        "owasp": "A05_security_misconfiguration",
        "title": "Default or Weak Admin Credentials",
        "pattern": r"(admin.*password|password.*admin|default.*cred)",
        "severity": "CRITICAL",
        "cwe": "CWE-1188",
        "description": "Default or weak administrator credentials detected in code or configuration.",
        "remediation": "Force credential change on first login. Never ship default credentials.",
    },
    # A07 — Identification and Authentication Failures
    {
        "id": "SEC-A07-001",
        "owasp": "A07_identification_auth_failures",
        "title": "JWT Algorithm 'none' Vulnerability",
        "pattern": r"(algorithm\s*=\s*['\"]none['\"]|alg.*none|\"alg\".*\"none\")",
        "severity": "CRITICAL",
        "cwe": "CWE-347",
        "description": "JWT 'none' algorithm allows forging tokens without a secret key.",
        "remediation": "Explicitly reject 'none' algorithm. Always specify allowed algorithms in JWT libraries.",
    },
    {
        "id": "SEC-A07-002",
        "owasp": "A07_identification_auth_failures",
        "title": "Missing Rate Limiting on Auth Endpoint",
        "pattern": r"@(app|router)\.post\s*\(['\"].*/(login|auth|token|signin)['\"]",
        "severity": "HIGH",
        "cwe": "CWE-307",
        "description": "Authentication endpoint without rate limiting is vulnerable to brute force attacks.",
        "remediation": "Apply rate limiting (e.g., slowapi or nginx limit_req) to authentication endpoints.",
    },
    {
        "id": "SEC-A07-003",
        "owasp": "A07_identification_auth_failures",
        "title": "Insecure Session Token (short/predictable)",
        "pattern": r"(session_?token|auth_?token)\s*=\s*(str\(|int\(|uuid\.uuid1|random\.random)",
        "severity": "HIGH",
        "cwe": "CWE-330",
        "description": "Session token generated with insufficient entropy or using predictable sources.",
        "remediation": "Use cryptographically secure random generation: secrets.token_urlsafe(32).",
    },
    # A08 — Software and Data Integrity Failures
    {
        "id": "SEC-A08-001",
        "owasp": "A08_software_data_integrity",
        "title": "Unsafe Deserialization",
        "pattern": r"(pickle\.loads?|yaml\.load\s*\([^,)]+\)|marshal\.loads?|jsonpickle\.decode)",
        "severity": "CRITICAL",
        "cwe": "CWE-502",
        "description": "Deserializing untrusted data with pickle/yaml.load/marshal allows arbitrary code execution.",
        "remediation": "Use yaml.safe_load instead of yaml.load. Avoid pickle for untrusted data. Use json for inter-service data.",
    },
    # A09 — Security Logging and Monitoring Failures
    {
        "id": "SEC-A09-001",
        "owasp": "A09_security_logging_monitoring",
        "title": "Authentication Event Not Logged",
        "pattern": r"def\s+(login|authenticate|verify_password)\s*\([^)]*\):[^#]*\n(?:(?!log|logger|audit|event).*\n){0,10}return\s+True",
        "severity": "MEDIUM",
        "cwe": "CWE-778",
        "description": "Authentication success/failure not logged. Prevents detection of brute force and credential stuffing attacks.",
        "remediation": "Log all authentication events (success and failure) with IP address, username, and timestamp.",
    },
    {
        "id": "SEC-A09-002",
        "owasp": "A09_security_logging_monitoring",
        "title": "Sensitive Data in Logs",
        "pattern": r"log\w*\.(info|debug|warning|error)\s*\([^)]*(?:password|secret|token|card|ssn|cpf)",
        "severity": "HIGH",
        "cwe": "CWE-532",
        "description": "Sensitive data (password, token, card number) written to logs. Accessible to anyone with log access.",
        "remediation": "Redact or mask sensitive fields before logging. Use structured logging with field-level masking.",
    },
    # A10 — SSRF
    {
        "id": "SEC-A10-001",
        "owasp": "A10_ssrf",
        "title": "Server-Side Request Forgery (SSRF)",
        "pattern": r"(requests\.(get|post|put|head)|urllib\.request\.urlopen|httpx\.(get|post))\s*\(\s*\w*(url|uri|endpoint|target)\s*[,)]",
        "severity": "HIGH",
        "cwe": "CWE-918",
        "description": "HTTP request made to a URL derived from user-controlled input. Can be used to probe internal services.",
        "remediation": "Validate and allowlist permitted URL destinations. Block requests to private IP ranges (10.x, 172.16.x, 192.168.x, 169.254.x).",
    },
]


def scan_source(source_code: str) -> List[Dict[str, Any]]:
    """
    Scan source code against all OWASP rules.
    Returns list of match dicts with rule metadata and line number.
    """
    matches = []
    lines = source_code.splitlines()
    for rule in OWASP_RULES:
        compiled = re.compile(rule["pattern"], re.IGNORECASE | re.MULTILINE)
        for line_no, line in enumerate(lines, start=1):
            if compiled.search(line):
                matches.append({
                    "rule_id": rule["id"],
                    "owasp": rule["owasp"],
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "cwe": rule["cwe"],
                    "description": rule["description"],
                    "remediation": rule["remediation"],
                    "line_number": line_no,
                    "evidence_line": line.strip(),
                })
    return matches
