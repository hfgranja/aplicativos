"""Ollama LLM adapter — reuses prompt structure from teacher-feedback.
Enriched with RAG context from MS-011 Knowledge Base.
Uses pec_shared.text_optimizer to reduce token spend before LLM calls."""
import json
import logging
from typing import Optional

import httpx

from pec_shared.text_optimizer import optimize, optimization_report

logger = logging.getLogger(__name__)

BASE_SYSTEM_PROMPT = """Você é um especialista em supervisão pedagógica no estado de São Paulo.
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

# Token budget reserved for system prompt + RAG chunks + response
_TRANSCRIPTION_TOKEN_BUDGET = 3000


def _build_system_prompt(
    knowledge_chunks: list[str],
    style_prompt: Optional[str],
    document_titles: list[str],
) -> str:
    parts = [BASE_SYSTEM_PROMPT]
    if style_prompt:
        parts.append(f"\nESTILO DE FEEDBACK CONFIGURADO:\n{style_prompt}")
    if knowledge_chunks:
        titles_str = ", ".join(document_titles) if document_titles else "base de conhecimento SEDUC"
        chunks_str = "\n\n---\n\n".join(knowledge_chunks)
        parts.append(f"\nCONTEXTO ADICIONAL (extraído de: {titles_str}):\n{chunks_str}")
    return "\n".join(parts)


def _build_user_prompt(transcription_text: str, observation_context: dict) -> str:
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
    knowledge_chunks: Optional[list[str]] = None,
    style_prompt: Optional[str] = None,
    document_titles: Optional[list[str]] = None,
) -> dict:
    # Optimize transcription text before sending to LLM
    optimized_text = optimize(transcription_text, max_tokens=_TRANSCRIPTION_TOKEN_BUDGET)
    report = optimization_report(transcription_text, optimized_text)
    logger.info(
        "LLM pre-send optimization: %d → %d est. tokens (%.1f%% saved)",
        report["estimated_tokens_before"],
        report["estimated_tokens_after"],
        report["reduction_pct"],
    )

    system_prompt = _build_system_prompt(
        knowledge_chunks=knowledge_chunks or [],
        style_prompt=style_prompt,
        document_titles=document_titles or [],
    )
    user_prompt = _build_user_prompt(optimized_text, observation_context)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
    }
    try:
        response = httpx.post(f"{base_url}/api/chat", json=payload, timeout=180.0)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        result = json.loads(content)
        result["_token_optimization"] = report
        return result
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}")
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Ollama request failed: {exc}")


def fetch_knowledge_context(
    knowledge_base_url: str,
    subject: str,
    grade: str,
    style_id: Optional[str] = None,
    max_chunks: int = 5,
) -> dict:
    """Call MS-011 to retrieve relevant document chunks and active style."""
    try:
        params = {"subject": subject, "grade": grade, "max_chunks": max_chunks}
        if style_id:
            params["style_id"] = style_id
        resp = httpx.get(
            f"{knowledge_base_url}/api/v1/knowledge/context",
            params=params,
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch knowledge context: %s", exc)
        return {"chunks": [], "document_titles": [], "active_style": None}
