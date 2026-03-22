"""
Hallucination detection check.
Detects factual inconsistency between prompt context and LLM output.
"""
import re
from typing import List
from engines.base import FindingData


def run(context: dict) -> List[FindingData]:
    """
    Checks for hallucination patterns in LLM outputs.
    context keys used:
      - llm_outputs: list of {"prompt": str, "context": str, "response": str}
      - source_code: str (fallback — scan for common hallucination-prone patterns)
    """
    findings = []
    outputs = context.get("llm_outputs", [])

    if outputs:
        for i, item in enumerate(outputs):
            prompt = item.get("prompt", "")
            ctx = item.get("context", "")
            response = item.get("response", "")

            # Heuristic: check for numeric/date claims in response not present in context
            numbers_in_response = set(re.findall(r'\b\d{4,}\b', response))
            numbers_in_context = set(re.findall(r'\b\d{4,}\b', ctx + prompt))
            hallucinated_numbers = numbers_in_response - numbers_in_context
            if hallucinated_numbers:
                findings.append(FindingData(
                    engine="ai_evals",
                    severity="HIGH",
                    category="ai_evals.hallucination",
                    title="Potential numeric hallucination detected",
                    description=(
                        f"LLM output contains numbers ({', '.join(list(hallucinated_numbers)[:5])}) "
                        f"not present in the provided context or prompt. This may indicate fabricated facts."
                    ),
                    evidence={"output_index": i, "hallucinated_numbers": list(hallucinated_numbers)},
                    pyramid_level=11,
                ))

            # Heuristic: look for definitive statements without grounding
            overconfident_phrases = [
                r'\baccording to the (study|report|research|data)\b',
                r'\bthe (fact|truth|reality) is\b',
                r'\bit is (known|proven|established) that\b',
            ]
            for pattern in overconfident_phrases:
                if re.search(pattern, response, re.IGNORECASE):
                    # Only flag if the grounding isn't in context
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match and match.group(0).lower() not in ctx.lower():
                        findings.append(FindingData(
                            engine="ai_evals",
                            severity="MEDIUM",
                            category="ai_evals.hallucination",
                            title="LLM makes ungrounded authoritative claim",
                            description=(
                                f"LLM uses authoritative language ('{match.group(0)}') without "
                                f"this claim appearing in the provided context."
                            ),
                            evidence={"output_index": i, "phrase": match.group(0)},
                            pyramid_level=11,
                        ))
                        break

    else:
        # Static analysis fallback: scan source code for LLM call patterns without output validation
        source = context.get("source_code", "")
        if source:
            _check_missing_validation(source, findings)

    return findings


def _check_missing_validation(source: str, findings: List[FindingData]) -> None:
    """Detect LLM calls that store the response without any validation."""
    # Pattern: client.messages.create / openai.chat.completions.create without
    # subsequent validation of the response
    llm_call_pattern = re.compile(
        r'(client\.messages\.create|openai\.chat|anthropic\.|llm\.invoke|chain\.run)',
        re.IGNORECASE,
    )
    validation_pattern = re.compile(
        r'(assert|validate|verify|check|if.*error|if.*none|if.*empty)',
        re.IGNORECASE,
    )

    lines = source.splitlines()
    for i, line in enumerate(lines):
        if llm_call_pattern.search(line):
            # Check the next 5 lines for any validation
            surrounding = "\n".join(lines[i + 1:i + 6])
            if not validation_pattern.search(surrounding):
                findings.append(FindingData(
                    engine="ai_evals",
                    severity="MEDIUM",
                    category="ai_evals.hallucination",
                    title="LLM output used without validation",
                    description=(
                        f"LLM call at line {i + 1} stores or uses the response directly "
                        f"without apparent validation. LLM outputs may hallucinate; "
                        f"validate before using in business logic."
                    ),
                    evidence={"line": i + 1, "snippet": line.strip()},
                    file_path="<source>",
                    line_number=i + 1,
                    pyramid_level=11,
                ))
