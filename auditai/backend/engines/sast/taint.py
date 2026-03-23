"""
Taint analysis — tracks flow from untrusted sources to dangerous sinks.
"""
import re
from typing import List, Dict, Set

TAINT_SOURCES = [
    r'request\.(args|form|json|data|files)\[',
    r'request\.get\s*\(',
    r'os\.environ\.get\s*\(',
    r'input\s*\(',
    r'sys\.argv',
    r'urllib\.parse\.(parse_qs|unquote)',
]

TAINT_SINKS = [
    (r'os\.system\s*\(', "CRITICAL", "Command Injection Sink", "CWE-78"),
    (r'subprocess\.(run|call|Popen)\s*\(', "HIGH", "Subprocess Sink", "CWE-78"),
    (r'eval\s*\(', "CRITICAL", "Code Injection Sink", "CWE-94"),
    (r'execute\s*\(', "HIGH", "SQL Execution Sink", "CWE-89"),
    (r'open\s*\(', "MEDIUM", "File Access Sink", "CWE-22"),
    (r'render_template\s*\(|render\s*\(', "HIGH", "Template Injection Sink", "CWE-94"),
    (r'redirect\s*\(', "MEDIUM", "Open Redirect Sink", "CWE-601"),
    (r'(log|logger)\.(info|debug|error|warning)\s*\(', "MEDIUM", "Log Injection Sink", "CWE-532"),
]


def taint_analysis(code: str) -> List[dict]:
    """
    Simplified taint analysis: flag lines that contain both a source pattern
    and a line within close proximity (±5 lines) that contains a sink pattern.
    A full interprocedural taint engine would require AST + CFG analysis.
    """
    findings = []
    lines = code.splitlines()

    # Find all lines with taint sources
    source_lines: Set[int] = set()
    for pattern in TAINT_SOURCES:
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                source_lines.add(i)

    # For each sink, check if a source is within ±10 lines
    for i, line in enumerate(lines):
        for sink_pattern, severity, title, cwe_id in TAINT_SINKS:
            if re.search(sink_pattern, line, re.IGNORECASE):
                nearby_sources = [s for s in source_lines if abs(s - i) <= 10]
                if nearby_sources:
                    source_line_num = nearby_sources[0] + 1
                    findings.append({
                        "severity": severity,
                        "category": "taint",
                        "title": f"Taint Flow to {title}",
                        "description": (
                            f"User-controlled data (line {source_line_num}) "
                            f"flows into {title} (line {i+1})"
                        ),
                        "cwe_id": cwe_id,
                        "line_number": i + 1,
                        "evidence": {
                            "sink_line": line.strip(),
                            "source_line": lines[nearby_sources[0]].strip(),
                            "source_line_number": source_line_num,
                        },
                        "score_penalty": 20,
                    })
                    break  # one finding per line per category

    return findings
