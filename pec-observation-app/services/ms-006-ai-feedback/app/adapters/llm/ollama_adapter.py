"""Ollama LLM adapter — reuses prompt structure from teacher-feedback."""
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um especialista em supervisão pedagógica no estado de São Paulo.
Sua tarefa é analisar a transcrição de uma aula observada e gerar um feedback formativo
para o professor, baseado em critérios pedagógicos do Currículo Paulista.

REGRAS OBRIGATÓRIAS:
- Não invente fatos que não estão na transcrição
- Não cite nomes de alunos
- Não use linguagem punitiva ou que caracterize incompetência
- Não faça rankings ou comparações com outros professores
- Toda observação deve ter evidência textual na transcrição
- Indique incertezas quando a transcrição não for clara
- Retorne APENAS JSON válido, sem texto extra

CRITÉRIOS DE AVALIAÇÃO (rubrica SEDUC-2026-v1):
1. Planejamento e alinhamento curricular
2. Clareza didática e condução da aula
3. Engajamento dos estudantes
4. Avaliação formativa
5. Gestão do tempo

FORMATO DE RESPOSTA (JSON exato):
{
  "summary": "string — resumo geral da aula em 2-3 frases",
  "strengths": [
    {"title": "string", "description": "string", "evidence": "trecho da transcrição"}
  ],
  "improvement_points": [
    {"title": "string", "description": "string", "evidence": "trecho da transcrição"}
  ],
  "evidence": [
    {"category": "string", "evidence_text": "string", "interpretation": "string",
     "confidence": "low|medium|high"}
  ],
  "suggested_action_plan": [
    {"action": "string", "owner": "Professor|PEC|Coordenação",
     "due_date_suggestion": "string", "expected_evidence": "string"}
  ],
  "risks_and_uncertainties": ["string"]
}"""


def _build_prompt(transcription_text: str, observation_context: dict) -> str:
    context_str = json.dumps(observation_context, ensure_ascii=False, indent=2)
    return (
        f"CONTEXTO DA OBSERVAÇÃO:\n{context_str}\n\n"
        f"TRANSCRIÇÃO DA AULA:\n{transcription_text}\n\n"
        "Gere o feedback formativo conforme as regras e formato especificado."
    )


def generate_feedback(
    transcription_text: str,
    observation_context: dict,
    base_url: str,
    model: str,
) -> dict:
    prompt = _build_prompt(transcription_text, observation_context)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
    }
    try:
        response = httpx.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}")
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Ollama request failed: {exc}")
