"""
Synthetic data generator — produces structurally valid, semantically realistic
test data from schema definitions, type annotations, or OpenAPI specs.
Uses LLM for semantic realism; falls back to rule-based generation.
"""
import json
import random
import re
import string
from typing import List, Dict, Any


SYNTHETIC_DATA_PROMPT = """You are a test data expert. Generate realistic synthetic test data.

Schema / Context:
{schema_description}

Generate {count} diverse test cases that:
1. Cover happy path (valid data)
2. Cover edge cases (boundary values, empty strings, max lengths)
3. Are realistic (not just "test", "foo", "1")
4. Include at least one case likely to trigger validation errors

Respond ONLY with JSON:
{{
  "cases": [
    {{
      "description": "what this case tests",
      "data": {{ ... }},
      "expected_valid": true
    }}
  ]
}}
"""


def generate(schema: Dict[str, Any], config: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate synthetic test data cases from a schema description.
    Returns list of {"description": str, "data": dict, "expected_valid": bool}.
    """
    cases = _generate_via_llm(schema, config, count)
    if cases:
        return cases
    return _generate_rule_based(schema, count)


def _generate_via_llm(schema: Dict[str, Any], config: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
    schema_description = json.dumps(schema, indent=2)[:2000]  # truncate to avoid token limits
    prompt = SYNTHETIC_DATA_PROMPT.format(
        schema_description=schema_description,
        count=count,
    )
    raw = _call_llm(prompt, config)
    if not raw:
        return []
    try:
        clean = re.sub(r"```[a-z]*\n?", "", raw).strip()
        data = json.loads(clean)
        return data.get("cases", [])
    except Exception:
        return []


def _generate_rule_based(schema: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
    """Generate test data purely from schema type definitions."""
    cases = []
    properties = schema.get("properties", schema.get("fields", {}))

    for i in range(count):
        data = {}
        for field_name, field_def in properties.items():
            field_type = field_def.get("type", "string") if isinstance(field_def, dict) else str(field_def)
            data[field_name] = _generate_field_value(field_type, field_name, i)

        description = "Valid data" if i < count * 0.7 else "Edge case data"
        expected_valid = i < count * 0.7
        cases.append({"description": description, "data": data, "expected_valid": expected_valid})

    return cases


def _generate_field_value(field_type: str, field_name: str, index: int) -> Any:
    """Generate a realistic value for a given field type."""
    field_type = field_type.lower()

    if "int" in field_type or "number" in field_type:
        edge_values = [0, -1, 1, 2**31 - 1, -(2**31)]
        if index < len(edge_values):
            return edge_values[index]
        return random.randint(1, 10000)

    if "float" in field_type:
        return round(random.uniform(0.01, 9999.99), 2)

    if "bool" in field_type:
        return index % 2 == 0

    if "email" in field_name.lower():
        return f"user{index}@example.com"

    if "name" in field_name.lower():
        names = ["Alice Johnson", "Bob Smith", "Carol Williams", "David Brown", "Eve Davis"]
        return names[index % len(names)]

    if "phone" in field_name.lower():
        return f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

    if "date" in field_name.lower():
        return f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

    if "amount" in field_name.lower() or "price" in field_name.lower():
        return round(random.uniform(1.00, 9999.99), 2)

    # Generic string
    if index == 0:
        return ""  # empty string edge case
    if index == 1:
        return "a" * 255  # max length edge case
    return "".join(random.choices(string.ascii_lowercase, k=random.randint(5, 20)))


def _call_llm(prompt: str, config: Dict[str, Any]) -> str:
    anthropic_key = config.get("anthropic_api_key", "")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
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
            timeout=45.0,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except Exception:
        pass
    return ""
