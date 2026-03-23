"""
Property-based test generator — infers Hypothesis @given properties from
function signatures, type hints, and docstrings.
"""
import ast
import json
import re
from typing import List, Dict, Any


PROPERTY_PROMPT = """You are an expert in property-based testing with Python Hypothesis.
Given this function, generate Hypothesis property tests.

Function:
```python
{function_code}
```

Function name: {function_name}
Args and types: {args_with_types}
Return type: {return_type}
Docstring: {docstring}

Generate 2-4 properties that should ALWAYS hold. Focus on:
1. Invariants (output type, output range, idempotency)
2. Round-trip properties (encode→decode == original)
3. Monotonicity (larger input → larger/smaller output)
4. Edge cases (empty input, zero, max values)

Respond ONLY with JSON:
{{
  "properties": [
    {{
      "name": "test_function_name_property_description",
      "code": "@given(...)\\ndef test_...:\\n    ...",
      "description": "what invariant this tests"
    }}
  ]
}}
"""

# Type annotation → Hypothesis strategy mapping
STRATEGY_MAP = {
    "str": "st.text()",
    "int": "st.integers()",
    "float": "st.floats(allow_nan=False)",
    "bool": "st.booleans()",
    "list": "st.lists(st.integers())",
    "dict": "st.dictionaries(st.text(), st.text())",
    "bytes": "st.binary()",
    "None": "st.none()",
}


def generate(functions: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate property-based tests for extracted functions."""
    results = []
    for func in functions[:8]:
        props = _generate_properties(func, config)
        if props:
            results.append({"function": func["name"], "properties": props, "source": "llm"})
        else:
            results.append({"function": func["name"], "properties": _template_properties(func), "source": "template"})
    return results


def _generate_properties(func: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    args_with_types = {arg: func.get("arg_types", {}).get(arg, "Any") for arg in func.get("args", [])}
    prompt = PROPERTY_PROMPT.format(
        function_code=func.get("source", ""),
        function_name=func["name"],
        args_with_types=json.dumps(args_with_types),
        return_type=func.get("return_type", "Any"),
        docstring=func.get("docstring", "No docstring"),
    )
    raw = _call_llm(prompt, config)
    if not raw:
        return []
    try:
        clean = re.sub(r"```[a-z]*\n?", "", raw).strip()
        data = json.loads(clean)
        return [p["code"] for p in data.get("properties", []) if "code" in p]
    except Exception:
        return []


def _template_properties(func: Dict[str, Any]) -> List[str]:
    """Generate template properties using Hypothesis without LLM."""
    name = func["name"]
    module = func.get("module", "module")
    args = func.get("args", [])
    arg_types = func.get("arg_types", {})

    strategies = []
    param_names = []
    for arg in args:
        ann = arg_types.get(arg, "str")
        strategy = STRATEGY_MAP.get(ann, "st.text()")
        strategies.append(f"{arg}={strategy}")
        param_names.append(arg)

    given_args = ", ".join(strategies) if strategies else "x=st.text()"
    call_args = ", ".join(param_names) if param_names else ""

    template = (
        f"from hypothesis import given, settings\n"
        f"from hypothesis import strategies as st\n"
        f"from {module} import {name}\n\n"
        f"@given({given_args})\n"
        f"@settings(max_examples=50)\n"
        f"def test_{name}_does_not_raise({', '.join(param_names) or 'x'}):\n"
        f"    \"\"\"Property: function should not raise on valid inputs.\"\"\"\n"
        f"    try:\n"
        f"        result = {name}({call_args})\n"
        f"        assert result is not None or True  # replace with real invariant\n"
        f"    except (ValueError, TypeError):\n"
        f"        pass  # expected for edge case inputs"
    )
    return [template]


def _call_llm(prompt: str, config: Dict[str, Any]) -> str:
    anthropic_key = config.get("anthropic_api_key", "")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception:
            pass

    ollama_url = config.get("ollama_url", "http://localhost:11434")
    ollama_model = config.get("ollama_model", "llama3.2")
    try:
        import httpx
        resp = httpx.post(
            f"{ollama_url}/api/generate",
            json={"model": ollama_model, "prompt": prompt, "stream": False},
            timeout=30.0,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except Exception:
        pass
    return ""
