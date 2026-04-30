"""MCP server — PEC Normas e Regras.

Exposes all norms, regulations, best practices, and training examples
catalogued in the PEC Observation system for use by LLM clients.

Transport: streamable-HTTP (accessible at /mcp)
Auth:      Bearer token via MCP_API_KEY env var (optional)
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP
from sqlalchemy import desc, func, text

from .config import settings
from .db import (EmbeddingRecord, FeedbackEvaluation, HealthSnapshot,
                 ModelBuild, evaluator_db, learning_db)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pec-mcp")

# ── Source-type labels (human-readable) ──────────────────────────────────────

SOURCE_LABELS = {
    "seduc_page":         "Norma/Regulamento SEDUC (crawl)",
    "approved_feedback":  "Feedback Aprovado (treino)",
    "best_practice":      "Boa Prática Pedagógica",
    "synthetic":          "Dado Sintético (augmentation)",
    "knowledge_document": "Documento da Base de Conhecimento",
    "crawl_page":         "Página Capturada (web)",
}

# ── MCP server ────────────────────────────────────────────────────────────────

mcp = FastMCP(
    "PEC Normas e Regras",
    instructions=(
        "Servidor de conhecimento do sistema PEC Observation. "
        "Contém todas as normas SEDUC catalogadas, exemplos de feedback aprovados, "
        "boas práticas pedagógicas e dados de treinamento do modelo pec-pedagogo."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_categories() -> str:
    """Lista todas as categorias de documentos catalogados com contagens."""
    with learning_db() as db:
        rows = (
            db.query(EmbeddingRecord.source_type, func.count().label("total"))
            .group_by(EmbeddingRecord.source_type)
            .order_by(desc("total"))
            .all()
        )
    result = []
    for row in rows:
        label = SOURCE_LABELS.get(row.source_type, row.source_type)
        result.append({"tipo": row.source_type, "descricao": label, "total": row.total})
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def list_norms(
    source_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    """Lista documentos catalogados com paginação.

    Args:
        source_type: Filtrar por tipo — seduc_page | approved_feedback |
                     best_practice | synthetic | knowledge_document | crawl_page.
                     Omitir para listar todos.
        page: Número da página (começa em 1).
        page_size: Documentos por página (max 50).
    """
    page_size = min(page_size, 50)
    offset = (page - 1) * page_size

    with learning_db() as db:
        q = db.query(EmbeddingRecord)
        if source_type:
            q = q.filter(EmbeddingRecord.source_type == source_type)
        total = q.count()
        records = (
            q.order_by(desc(EmbeddingRecord.created_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

    items = []
    for r in records:
        meta = r.metadata_ or {}
        items.append({
            "id":             str(r.id),
            "tipo":           r.source_type,
            "titulo":         meta.get("title", meta.get("url", r.source_id)),
            "fonte":          meta.get("url", r.source_id),
            "qualidade":      round(r.quality_score, 3) if r.quality_score else None,
            "peso_selecao":   round(r.selection_weight, 3) if r.selection_weight else None,
            "criado_em":      r.created_at.isoformat() if r.created_at else None,
            "trecho":         r.content[:300] + "…" if len(r.content) > 300 else r.content,
        })

    return json.dumps(
        {"total": total, "pagina": page, "por_pagina": page_size, "itens": items},
        ensure_ascii=False, indent=2,
    )


@mcp.tool()
def get_norm(norm_id: str) -> str:
    """Retorna o conteúdo completo de um documento pelo seu ID (UUID).

    Args:
        norm_id: UUID do documento retornado por list_norms ou search_norms.
    """
    with learning_db() as db:
        record = db.query(EmbeddingRecord).filter(
            EmbeddingRecord.id == norm_id
        ).first()

    if not record:
        return json.dumps({"erro": f"Documento {norm_id} não encontrado."})

    meta = record.metadata_ or {}
    return json.dumps({
        "id":           str(record.id),
        "tipo":         record.source_type,
        "descricao_tipo": SOURCE_LABELS.get(record.source_type, record.source_type),
        "titulo":       meta.get("title", meta.get("url", record.source_id)),
        "fonte_url":    meta.get("url", record.source_id),
        "qualidade":    round(record.quality_score, 4) if record.quality_score else None,
        "peso_selecao": round(record.selection_weight, 4) if record.selection_weight else None,
        "metadata":     meta,
        "conteudo":     record.content,
        "criado_em":    record.created_at.isoformat() if record.created_at else None,
        "atualizado_em": record.updated_at.isoformat() if record.updated_at else None,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def search_norms(
    query: str,
    source_type: Optional[str] = None,
    limit: int = 10,
    use_semantic: bool = True,
) -> str:
    """Busca documentos por similaridade semântica ou texto.

    Usa embeddings vetoriais (via Ollama nomic-embed-text) quando
    use_semantic=True. Cai automaticamente para busca por texto se o
    Ollama não estiver disponível.

    Args:
        query: Texto de busca (ex: "avaliação formativa", "plano de aula PEC").
        source_type: Filtrar por tipo de fonte (opcional).
        limit: Número máximo de resultados (max 30).
        use_semantic: True = similaridade vetorial; False = texto (ILIKE).
    """
    limit = min(limit, 30)
    embedding = None

    if use_semantic:
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json={"model": settings.ollama_embedding_model, "prompt": query},
                )
                resp.raise_for_status()
                embedding = resp.json()["embedding"]
        except Exception as exc:
            logger.warning("Ollama unavailable for embedding (%s) — falling back to text search", exc)

    with learning_db() as db:
        q = db.query(EmbeddingRecord)
        if source_type:
            q = q.filter(EmbeddingRecord.source_type == source_type)
        q = q.filter(EmbeddingRecord.content != None)  # noqa: E711

        if embedding:
            # pgvector cosine distance — lower = more similar
            q = q.order_by(
                EmbeddingRecord.embedding.cosine_distance(embedding)
            ).limit(limit)
            mode = "semantica"
        else:
            pattern = f"%{query}%"
            q = q.filter(EmbeddingRecord.content.ilike(pattern)).limit(limit)
            mode = "texto"

        records = q.all()

    items = []
    for r in records:
        meta = r.metadata_ or {}
        items.append({
            "id":        str(r.id),
            "tipo":      r.source_type,
            "titulo":    meta.get("title", meta.get("url", r.source_id)),
            "fonte":     meta.get("url", r.source_id),
            "qualidade": round(r.quality_score, 3) if r.quality_score else None,
            "trecho":    r.content[:400] + "…" if len(r.content) > 400 else r.content,
        })

    return json.dumps(
        {"query": query, "modo_busca": mode, "resultados": len(items), "itens": items},
        ensure_ascii=False, indent=2,
    )


@mcp.tool()
def list_training_examples(
    min_quality: float = 0.0,
    include_synthetic: bool = True,
    limit: int = 20,
) -> str:
    """Lista exemplos usados para treinar o modelo pec-pedagogo.

    Args:
        min_quality: Score mínimo de qualidade (0.0–1.0). Use 0.7 para
                     ver apenas exemplos de alta qualidade.
        include_synthetic: Incluir dados sintéticos gerados por augmentation.
        limit: Número máximo de exemplos (max 100).
    """
    limit = min(limit, 100)
    types = ["approved_feedback"]
    if include_synthetic:
        types.append("synthetic")

    with learning_db() as db:
        records = (
            db.query(EmbeddingRecord)
            .filter(
                EmbeddingRecord.source_type.in_(types),
                EmbeddingRecord.quality_score >= min_quality,
            )
            .order_by(desc(EmbeddingRecord.selection_weight))
            .limit(limit)
            .all()
        )

    items = []
    for r in records:
        meta = r.metadata_ or {}
        items.append({
            "id":             str(r.id),
            "tipo":           r.source_type,
            "qualidade":      round(r.quality_score, 4) if r.quality_score else None,
            "peso_selecao":   round(r.selection_weight, 4) if r.selection_weight else None,
            "observation_id": meta.get("observation_id"),
            "sintetico":      r.source_type == "synthetic",
            "trecho":         r.content[:500] + "…" if len(r.content) > 500 else r.content,
            "criado_em":      r.created_at.isoformat() if r.created_at else None,
        })

    return json.dumps(
        {"total_retornado": len(items), "filtro_qualidade_min": min_quality, "exemplos": items},
        ensure_ascii=False, indent=2,
    )


@mcp.tool()
def get_model_health() -> str:
    """Retorna o último relatório de saúde do modelo pec-pedagogo (MS-014).

    Inclui: score médio de qualidade, tendência, status (stable/improving/
    declining/degraded) e contagem de avaliações recentes.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{settings.evaluator_service_url}/api/v1/evaluator/health-report")
            resp.raise_for_status()
            return json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Fallback: query local DB snapshot
    with evaluator_db() as db:
        snap = (
            db.query(HealthSnapshot)
            .order_by(desc(HealthSnapshot.created_at))
            .first()
        )
    if not snap:
        return json.dumps({"aviso": "Nenhum snapshot de saúde disponível ainda."})

    return json.dumps({
        "status":          snap.status,
        "qualidade_media": round(snap.mean_quality, 4),
        "tendencia":       round(snap.trend, 4),
        "amostras":        snap.sample_count,
        "capturado_em":    snap.created_at.isoformat(),
        "detalhes":        snap.details,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_model_builds(limit: int = 5) -> str:
    """Histórico de reconstruções do modelo pec-pedagogo.

    Args:
        limit: Número de registros mais recentes (max 20).
    """
    limit = min(limit, 20)
    with learning_db() as db:
        builds = (
            db.query(ModelBuild)
            .order_by(desc(ModelBuild.created_at))
            .limit(limit)
            .all()
        )

    items = [
        {
            "id":              str(b.id),
            "modelo":          b.model_name,
            "base":            b.base_model,
            "exemplos":        b.examples_count,
            "status":          b.status,
            "erro":            b.error,
            "construido_em":   b.built_at.isoformat() if b.built_at else None,
            "iniciado_em":     b.created_at.isoformat() if b.created_at else None,
        }
        for b in builds
    ]
    return json.dumps({"builds": items}, ensure_ascii=False, indent=2)


@mcp.tool()
def get_statistics() -> str:
    """Estatísticas globais da base de conhecimento e dados de treinamento."""
    with learning_db() as db:
        by_type = (
            db.query(EmbeddingRecord.source_type, func.count().label("n"))
            .group_by(EmbeddingRecord.source_type)
            .all()
        )
        total = sum(r.n for r in by_type)
        with_quality = (
            db.query(func.count())
            .filter(EmbeddingRecord.quality_score.isnot(None))
            .scalar()
        )
        avg_quality = (
            db.query(func.avg(EmbeddingRecord.quality_score))
            .filter(EmbeddingRecord.quality_score.isnot(None))
            .scalar()
        )
        last_build = (
            db.query(ModelBuild)
            .filter(ModelBuild.status == "success")
            .order_by(desc(ModelBuild.built_at))
            .first()
        )

    with evaluator_db() as db:
        total_evals = db.query(func.count(FeedbackEvaluation.id)).scalar()
        last_snap = (
            db.query(HealthSnapshot)
            .order_by(desc(HealthSnapshot.created_at))
            .first()
        )

    return json.dumps({
        "base_de_conhecimento": {
            "total_documentos":  total,
            "com_embedding":     total,
            "com_qualidade":     with_quality,
            "qualidade_media":   round(float(avg_quality), 4) if avg_quality else None,
            "por_tipo":          {r.source_type: r.n for r in by_type},
        },
        "modelo_pec_pedagogo": {
            "ultima_construcao": {
                "status":      last_build.status if last_build else "sem registro",
                "exemplos":    last_build.examples_count if last_build else 0,
                "construido_em": last_build.built_at.isoformat() if last_build and last_build.built_at else None,
            },
            "total_avaliacoes": total_evals,
            "saude_atual": {
                "status":   last_snap.status if last_snap else "desconhecido",
                "qualidade": round(last_snap.mean_quality, 4) if last_snap else None,
                "tendencia": round(last_snap.trend, 4) if last_snap else None,
            } if last_snap else None,
        },
        "gerado_em": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def list_seduc_sources() -> str:
    """Lista todas as fontes SEDUC que foram crawleadas e indexadas."""
    with learning_db() as db:
        records = (
            db.query(EmbeddingRecord)
            .filter(EmbeddingRecord.source_type.in_(["seduc_page", "crawl_page"]))
            .order_by(desc(EmbeddingRecord.created_at))
            .all()
        )

    sources = {}
    for r in records:
        meta = r.metadata_ or {}
        url = meta.get("url", r.source_id)
        # Deduplicate by URL, keep most recent
        if url not in sources:
            sources[url] = {
                "id":       str(r.id),
                "url":      url,
                "titulo":   meta.get("title", url),
                "tipo":     r.source_type,
                "capturado_em": r.created_at.isoformat() if r.created_at else None,
                "trecho":   r.content[:200] + "…" if len(r.content) > 200 else r.content,
            }

    return json.dumps(
        {"total_fontes": len(sources), "fontes": list(sources.values())},
        ensure_ascii=False, indent=2,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("pec://catalogo/resumo")
def catalogue_summary() -> str:
    """Resumo textual de todo o catálogo de normas e dados de treinamento."""
    with learning_db() as db:
        by_type = (
            db.query(EmbeddingRecord.source_type, func.count().label("n"))
            .group_by(EmbeddingRecord.source_type)
            .all()
        )
        total = sum(r.n for r in by_type)
        avg_q = (
            db.query(func.avg(EmbeddingRecord.quality_score))
            .filter(EmbeddingRecord.quality_score.isnot(None))
            .scalar()
        )

    lines = [
        "# Catálogo PEC — Normas, Regras e Dados de Treinamento",
        "",
        f"Total de documentos indexados: {total}",
        f"Qualidade média dos exemplos avaliados: {round(float(avg_q), 3) if avg_q else 'N/A'}",
        "",
        "## Distribuição por tipo:",
    ]
    for row in sorted(by_type, key=lambda r: r.n, reverse=True):
        label = SOURCE_LABELS.get(row.source_type, row.source_type)
        lines.append(f"  - {label}: {row.n} documentos")

    lines += [
        "",
        "## Ferramentas disponíveis:",
        "  - list_categories      → categorias com contagens",
        "  - list_norms           → listagem paginada",
        "  - get_norm             → conteúdo completo por ID",
        "  - search_norms         → busca semântica ou por texto",
        "  - list_training_examples → exemplos de treinamento",
        "  - list_seduc_sources   → páginas SEDUC crawleadas",
        "  - get_model_health     → saúde atual do modelo",
        "  - get_model_builds     → histórico de reconstruções",
        "  - get_statistics       → estatísticas globais",
    ]
    return "\n".join(lines)


@mcp.resource("pec://modelo/saude")
def model_health_resource() -> str:
    """Relatório de saúde atual do modelo pec-pedagogo."""
    return get_model_health()


@mcp.resource("pec://treinamento/resumo")
def training_summary() -> str:
    """Resumo dos dados de treinamento aprovados e sintéticos."""
    with learning_db() as db:
        approved = (
            db.query(func.count(), func.avg(EmbeddingRecord.quality_score))
            .filter(EmbeddingRecord.source_type == "approved_feedback")
            .first()
        )
        synthetic = (
            db.query(func.count())
            .filter(EmbeddingRecord.source_type == "synthetic")
            .scalar()
        )
        top_examples = (
            db.query(EmbeddingRecord)
            .filter(EmbeddingRecord.source_type == "approved_feedback")
            .filter(EmbeddingRecord.quality_score.isnot(None))
            .order_by(desc(EmbeddingRecord.selection_weight))
            .limit(5)
            .all()
        )

    lines = [
        "# Dados de Treinamento — pec-pedagogo",
        "",
        f"Feedbacks aprovados: {approved[0]}",
        f"Qualidade média aprovados: {round(float(approved[1]), 3) if approved[1] else 'N/A'}",
        f"Dados sintéticos (augmentation): {synthetic}",
        "",
        "## Top 5 exemplos por peso de seleção:",
    ]
    for ex in top_examples:
        meta = ex.metadata_ or {}
        lines.append(
            f"  [{round(ex.selection_weight, 3) if ex.selection_weight else '?'}] "
            f"{meta.get('observation_id', str(ex.id)[:8])} — "
            f"qualidade={round(ex.quality_score, 3) if ex.quality_score else 'N/A'}"
        )

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json as _json
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy", "service": "pec-mcp"})

    asgi_app = Starlette(routes=[
        Route("/health", health),
        Mount("/mcp", app=mcp.streamable_http_app()),
        # Root redirect for convenience
        Mount("/",     app=mcp.streamable_http_app()),
    ])

    logger.info("Starting PEC MCP server on %s:%s", settings.server_host, settings.server_port)
    uvicorn.run(
        asgi_app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="info",
    )
