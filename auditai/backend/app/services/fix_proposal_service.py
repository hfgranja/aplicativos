"""
AI code fix proposal service — uses Ollama or Claude API.
"""
import json
import re
from datetime import datetime
from typing import AsyncGenerator, Optional
import httpx
from app.config import settings
from app.models.finding import Finding

FIX_PROMPT_TEMPLATE = """You are an expert software security engineer. Analyze the following finding and provide a concrete code fix.

Finding:
- Severity: {severity}
- Category: {category}
- Title: {title}
- Description: {description}
- CWE: {cwe_id}
- File: {file_path}
- Line: {line_number}

Code context:
```
{code_context}
```

Respond ONLY with a JSON object (no markdown) in this exact format:
{{
  "explanation": "why this is a problem",
  "before_code": "original problematic code snippet",
  "after_code": "corrected code snippet",
  "diff": "unified diff format",
  "rationale": "what the fix does and why it is correct",
  "confidence": 0.85
}}
"""


def generate_fix_proposal(finding: Finding) -> Optional[dict]:
    """Synchronous fix generation via Ollama."""
    try:
        prompt = FIX_PROMPT_TEMPLATE.format(
            severity=finding.severity or "UNKNOWN",
            category=finding.category or "UNKNOWN",
            title=finding.title,
            description=finding.description or "",
            cwe_id=finding.cwe_id or "N/A",
            file_path=finding.file_path or "N/A",
            line_number=finding.line_number or "N/A",
            code_context=_extract_code_context(finding),
        )

        # Try Ollama first
        response = httpx.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60.0,
        )

        if response.status_code == 200:
            raw = response.json().get("response", "")
            return _parse_fix_response(raw, "ollama/" + settings.OLLAMA_MODEL)

    except Exception:
        pass

    # Fallback to Claude API if configured
    if settings.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            return _parse_fix_response(raw, "claude-sonnet-4-6")
        except Exception:
            pass

    # Fallback to FixSynthesizer (CodeT5) when no LLM endpoint is available
    try:
        from engines.neural.models import ModelRegistry
        synthesizer = ModelRegistry.get_instance().get_synthesizer()
        code_context = _extract_code_context(finding)
        result = synthesizer.synthesize(
            code_context,
            f"{finding.category or ''} {finding.title}",
        )
        if result.fixed_code:
            return {
                "explanation": f"{finding.category}: {finding.title}",
                "before_code": code_context,
                "after_code": result.fixed_code,
                "diff": result.diff,
                "rationale": result.explanation,
                "confidence": round(result.confidence, 2),
                "generated_by": f"FixSynthesizer/{result.method}",
                "generated_at": datetime.utcnow().isoformat(),
            }
    except Exception:
        pass

    return None


async def stream_fix_proposal(finding: Finding) -> AsyncGenerator[dict, None]:
    """Streaming fix generation via Ollama SSE."""
    prompt = FIX_PROMPT_TEMPLATE.format(
        severity=finding.severity or "UNKNOWN",
        category=finding.category or "UNKNOWN",
        title=finding.title,
        description=finding.description or "",
        cwe_id=finding.cwe_id or "N/A",
        file_path=finding.file_path or "N/A",
        line_number=finding.line_number or "N/A",
        code_context=_extract_code_context(finding),
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.OLLAMA_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": True},
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield {"token": token, "done": data.get("done", False)}
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        yield {"error": str(e), "done": True}


def _extract_code_context(finding: Finding) -> str:
    evidence = finding.evidence or {}
    return evidence.get("code_snippet", finding.description or "No code context available")


def _parse_fix_response(raw: str, model: str) -> Optional[dict]:
    # Try to extract JSON from response
    try:
        # Strip markdown code blocks if present
        clean = re.sub(r"```[a-z]*\n?", "", raw).strip()
        data = json.loads(clean)
        data["generated_by"] = model
        data["generated_at"] = datetime.utcnow().isoformat()
        if "confidence" not in data:
            data["confidence"] = 0.7
        return data
    except Exception:
        return {
            "explanation": raw[:500],
            "before_code": "",
            "after_code": "",
            "diff": "",
            "rationale": "Raw LLM output — manual review required",
            "confidence": 0.3,
            "generated_by": model,
            "generated_at": datetime.utcnow().isoformat(),
        }
