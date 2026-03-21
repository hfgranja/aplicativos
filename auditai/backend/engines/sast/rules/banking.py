"""
Banking domain SAST rules — financial system invariants and compliance patterns.
"""
import re
from typing import List, Tuple

BANKING_RULES: List[Tuple] = [
    # Float arithmetic in money
    (r'\bfloat\s*\(.*amount|float\s*\(.*balance|float\s*\(.*price',
     "HIGH", "Float Arithmetic in Money",
     "Never use float for monetary values — use Decimal or integer cents", "CWE-681", 20),
    (r'\d+\.\d+\s*\*\s*\d+\.\d+', "MEDIUM", "Potential Float Multiplication in Finance",
     "Float multiplication may cause rounding errors in financial calculations", "CWE-681", 10),
    # Idempotency
    (r'def\s+(process_payment|charge|debit|credit|transfer)\s*\([^)]*\):(?!.*idempotent)',
     "MEDIUM", "Missing Idempotency Check",
     "Financial operation may not be idempotent — add idempotency key check", "CWE-841", 10),
    # Balance validation
    (r'balance\s*-=\s*amount(?!\s*(if|when|assert|raise|check))',
     "HIGH", "Missing Balance Validation Before Debit",
     "Deduct from balance without prior validation may cause negative balance", "CWE-841", 15),
    # Log sensitive financial data
    (r'(log|print)\s*\(.*?(card_number|pan|cvv|account_number)',
     "CRITICAL", "PCI DSS Violation: Financial Data in Logs",
     "Card or account data must never appear in logs", "CWE-532", 25),
    # Hardcoded financial limits
    (r'(limit|max_amount|min_amount|threshold)\s*=\s*\d+',
     "LOW", "Hardcoded Financial Limit",
     "Financial limits should be configurable, not hardcoded", "CWE-798", 5),
    # Missing transaction atomicity
    (r'def\s+transfer\s*\([^)]*\):(?!.*transaction|atomic|begin)',
     "HIGH", "Missing Transaction Atomicity",
     "Transfer operation should be wrapped in a database transaction", "CWE-362", 20),
    # Concurrency in balance update
    (r'balance\s*=\s*balance\s*[+-]', "MEDIUM", "Race Condition Risk in Balance Update",
     "Non-atomic balance update is vulnerable to race conditions — use SELECT FOR UPDATE", "CWE-362", 15),
]


def scan_banking(code: str) -> List[dict]:
    findings = []
    lines = code.splitlines()
    for pattern, severity, title, description, cwe_id, penalty in BANKING_RULES:
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    "severity": severity,
                    "category": "banking",
                    "title": title,
                    "description": description,
                    "cwe_id": cwe_id,
                    "line_number": i,
                    "evidence": {"code_snippet": line.strip()},
                    "score_penalty": penalty,
                })
    return findings
