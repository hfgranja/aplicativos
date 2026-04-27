"""Build and push an Ollama Modelfile from accumulated approved feedback examples."""
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models.embedding import EmbeddingRecord, ModelBuild

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Você é PEC-Pedagogo, um assistente especializado em supervisão pedagógica
no sistema educacional do Estado de São Paulo.

Sua missão é analisar transcrições de aulas observadas e gerar feedback formativo de alta
qualidade para professores, baseado no Currículo Paulista e nas melhores práticas pedagógicas
consolidadas pela SEDUC-SP.

PRINCÍPIOS INEGOCIÁVEIS:
- Nunca invente fatos; toda observação precisa de evidência textual
- Nunca cite nomes de alunos
- Nunca use linguagem punitiva ou que caracterize incompetência
- Indique incertezas quando a transcrição for ambígua
- Retorne sempre JSON válido conforme o schema acordado

CRITÉRIOS DE AVALIAÇÃO (rubrica SEDUC-2026-v1):
1. Planejamento e alinhamento curricular
2. Clareza didática e condução da aula
3. Engajamento dos estudantes
4. Avaliação formativa
5. Gestão do tempo e ritmo

Você aprendeu com centenas de observações reais e feedbacks aprovados por PECs experientes."""


def _build_modelfile(base_model: str, examples: list[EmbeddingRecord]) -> str:
    lines = [f"FROM {base_model}", "", f'SYSTEM """{_SYSTEM_PROMPT}"""', ""]

    # Include approved feedback examples as few-shot turns
    for rec in examples:
        meta = rec.metadata_ or {}
        transcription_snippet = meta.get("transcription_snippet", "")
        feedback_json = meta.get("feedback_json", "")
        if not transcription_snippet or not feedback_json:
            continue
        lines += [
            "MESSAGE user " + repr(
                f"TRANSCRIÇÃO: {transcription_snippet}\n\nGere o feedback formativo."
            ),
            "MESSAGE assistant " + repr(feedback_json),
            "",
        ]

    lines += [
        "PARAMETER temperature 0.3",
        "PARAMETER top_p 0.9",
        "PARAMETER num_predict 2048",
    ]
    return "\n".join(lines)


def rebuild_model(
    db: Session,
    base_url: str,
    base_model: str,
    pec_model_name: str,
    max_examples: int = 20,
) -> ModelBuild:
    build = ModelBuild(
        model_name=pec_model_name,
        base_model=base_model,
        examples_count="0",
        status="building",
    )
    db.add(build)
    db.commit()

    try:
        examples = (
            db.query(EmbeddingRecord)
            .filter_by(source_type="approved_feedback")
            .order_by(EmbeddingRecord.created_at.desc())
            .limit(max_examples)
            .all()
        )
        build.examples_count = str(len(examples))
        modelfile_content = _build_modelfile(base_model, examples)

        resp = httpx.post(
            f"{base_url}/api/create",
            json={"name": pec_model_name, "modelfile": modelfile_content},
            timeout=300.0,
        )
        resp.raise_for_status()

        build.status = "success"
        build.built_at = datetime.now(timezone.utc)
        logger.info(
            "Rebuilt Ollama model '%s' with %d examples", pec_model_name, len(examples)
        )
    except Exception as exc:
        build.status = "failed"
        build.error = str(exc)
        logger.error("Model rebuild failed: %s", exc)

    db.commit()
    db.refresh(build)
    return build
