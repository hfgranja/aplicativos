"""
Unit test generator — produces pytest unit tests from function signatures.
Uses Claude API or Ollama; falls back to AST-based template generation.
"""
import ast
import json
import re
from typing import List, Dict, Any


UNIT_TEST_PROMPT = """You are an expert Python test engineer. Given this function, generate pytest unit tests.

Function:
```python
{function_code}
```

Module: {module_name}
Function: {function_name}
Args: {args}
Return type: {return_type}
Docstring: {docstring}

Respond ONLY with a JSON object:
{{
  "tests": [
    {{
      "name": "test_function_name_scenario",
      "code": "def test_...:\\n    ...",
      "description": "what this test verifies"
    }}
  ]
}}

Generate 3-5 tests covering: happy path, edge cases (None, empty, 0, max int), and error cases.
"""


def generate(functions: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate unit tests for a list of extracted function descriptors.
    Returns list of {"function": str, "tests": list[str], "source": str}.
    """
    results = []
    for func in functions[:10]:  # cap at 10 functions to avoid LLM cost explosion
        tests = _generate_for_function(func, config)
        if tests:
            results.append({"function": func["name"], "tests": tests, "source": "llm"})
        else:
            # AST-based fallback
            results.append({"function": func["name"], "tests": _template_tests(func), "source": "template"})
    return results


def _generate_for_function(func: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    prompt = UNIT_TEST_PROMPT.format(
        function_code=func.get("source", ""),
        module_name=func.get("module", "unknown"),
        function_name=func["name"],
        args=", ".join(func.get("args", [])),
        return_type=func.get("return_type", "Any"),
        docstring=func.get("docstring", "No docstring"),
    )
    raw = _call_llm(prompt, config)
    if not raw:
        return []
    try:
        clean = re.sub(r"```[a-z]*\n?", "", raw).strip()
        data = json.loads(clean)
        return [t["code"] for t in data.get("tests", []) if "code" in t]
    except Exception:
        return []


def _call_llm(prompt: str, config: Dict[str, Any]) -> str:
    """Try Claude API then Ollama; return raw response or empty string."""
    anthropic_key = config.get("anthropic_api_key") or ""
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


def _template_tests(func: Dict[str, Any]) -> List[str]:
    """Generate template unit tests without LLM."""
    name = func["name"]
    module = func.get("module", "module")
    args = func.get("args", [])
    none_args = ", ".join(["None"] * len(args))
    default_args = ", ".join([f'""' if "str" in func.get("arg_types", {}).get(a, "") else "0" for a in args])

    tests = [
        f"def test_{name}_basic():\n    from {module} import {name}\n    # TODO: add assertions\n    result = {name}({default_args})\n    assert result is not None",
        f"def test_{name}_with_none():\n    from {module} import {name}\n    # TODO: verify None handling\n    try:\n        {name}({none_args})\n    except (TypeError, ValueError):\n        pass  # expected",
    ]
    return tests
