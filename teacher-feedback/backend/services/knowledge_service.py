import json
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from models import KnowledgeBase, ActionPlanResult, Observation
from services.llm_service import compute_section_scores, compute_ef1_scores, infer_grade_band


def index_observation(db: Session, obs_id: str) -> int:
    """Extract and index useful content from an observation into knowledge_base.
    Returns number of entries indexed."""
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        return 0

    indexed = 0
    scores = compute_section_scores(obs)
    total_score = scores.get("total", 0)
    grade_band = infer_grade_band(obs.teacher.grade if obs.teacher else "")
    subject = obs.teacher.subject if obs.teacher else ""

    # Index feedback pontos_fortes + proximos_passos if feedback_raw exists
    if obs.feedback_raw:
        try:
            feedback = json.loads(obs.feedback_raw)
            source_type = "best_practice" if total_score >= 75 else "feedback"

            # Index pontos_fortes
            pontos = feedback.get("pontos_fortes", [])
            if pontos:
                content = "Pontos fortes identificados:\n" + "\n".join(f"- {p}" for p in pontos)
                _upsert_entry(db, obs, source_type, subject, grade_band, content, total_score)
                indexed += 1

            # Index proximos_passos
            passos = feedback.get("proximos_passos", [])
            if passos:
                content = "Próximos passos recomendados:\n" + "\n".join(f"- {p}" for p in passos)
                _upsert_entry(db, obs, "feedback", subject, grade_band, content, total_score)
                indexed += 1

            # Index areas_desenvolvimento
            areas = feedback.get("areas_desenvolvimento", [])
            if areas:
                content = "Áreas de desenvolvimento:\n" + "\n".join(
                    f"- {a.get('area', '')}: {a.get('sugestao_concreta', '')}"
                    for a in areas if isinstance(a, dict)
                )
                _upsert_entry(db, obs, "feedback", subject, grade_band, content, total_score)
                indexed += 1

            # EF I dominios if present
            dominios = feedback.get("dominios", {})
            if dominios:
                ef1_content_parts = []
                for dom, info in dominios.items():
                    if isinstance(info, dict) and info.get("recomendacao"):
                        ef1_content_parts.append(f"[{dom.upper()}] {info['recomendacao']}")
                if ef1_content_parts:
                    content = "Recomendações EF I:\n" + "\n".join(ef1_content_parts)
                    _upsert_entry(db, obs, source_type, subject, "ef1", content, total_score)
                    indexed += 1

        except (json.JSONDecodeError, TypeError):
            pass

    # Index transcript snippets (first 3 meaningful segments)
    if obs.transcript:
        segments = [s.strip() for s in obs.transcript.split('\n') if len(s.strip()) > 80][:3]
        for seg in segments:
            _upsert_entry(db, obs, "transcript", subject, grade_band, seg, total_score)
            indexed += 1

    db.commit()
    return indexed


def _upsert_entry(db: Session, obs: Observation, source_type: str,
                  subject: str, grade_band: str, content: str, score: int):
    entry = KnowledgeBase(
        id=str(uuid.uuid4()),
        teacher_id=obs.teacher_id,
        observation_id=obs.id,
        source_type=source_type,
        subject=subject or "",
        grade_band=grade_band or "",
        content=content,
        score_at_time=score,
        created_at=datetime.utcnow(),
    )
    db.add(entry)


def get_best_practices(db: Session, subject: str = "", grade_band: str = "", limit: int = 5) -> List[dict]:
    """Returns best practices from high-performing teachers."""
    query = db.query(KnowledgeBase).filter(KnowledgeBase.source_type == "best_practice")
    if subject:
        query = query.filter(KnowledgeBase.subject == subject)
    if grade_band:
        query = query.filter(KnowledgeBase.grade_band == grade_band)
    entries = query.order_by(KnowledgeBase.score_at_time.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "content": e.content,
            "score_at_time": e.score_at_time,
            "subject": e.subject,
            "grade_band": e.grade_band,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


def get_similar_context(db: Session, subject: str, grade: str,
                        weak_sections: Optional[str] = None, limit: int = 5) -> List[dict]:
    """Find teachers in similar context who improved weak sections."""
    grade_band = infer_grade_band(grade)
    query = db.query(KnowledgeBase).filter(
        KnowledgeBase.subject == subject,
        KnowledgeBase.grade_band == grade_band,
        KnowledgeBase.source_type.in_(["best_practice", "action_plan"]),
    )
    if weak_sections:
        secs = [s.strip() for s in weak_sections.split(",") if s.strip()]
        if secs:
            from sqlalchemy import or_
            filters = [KnowledgeBase.content.ilike(f"%{sec}%") for sec in secs]
            query = query.filter(or_(*filters))

    entries = query.order_by(KnowledgeBase.score_at_time.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "content": e.content,
            "score_at_time": e.score_at_time,
            "source_type": e.source_type,
        }
        for e in entries
    ]


def index_action_result(db: Session, action_result: ActionPlanResult):
    """Index a successfully executed action plan into knowledge base."""
    if action_result.status != "realizado":
        return
    if not (action_result.delta_score and action_result.delta_score > 0):
        return

    obs = db.query(Observation).filter(Observation.id == action_result.observation_id).first()
    if not obs:
        return

    grade_band = infer_grade_band(obs.teacher.grade if obs.teacher else "")
    subject = obs.teacher.subject if obs.teacher else ""
    notes = action_result.result_notes or ""
    content = (
        f"Combinado executado com sucesso (+{action_result.delta_score}pts):\n"
        f"Ação: {action_result.action_text}\n"
        f"Responsável: {action_result.responsible}\n"
        f"Resultado: {notes}"
    )
    _upsert_entry(db, obs, "action_plan", subject, grade_band, content,
                  action_result.score_after or 0)
    db.commit()


def get_teacher_action_results(db: Session, teacher_id: str) -> List[dict]:
    results = db.query(ActionPlanResult).filter(
        ActionPlanResult.teacher_id == teacher_id
    ).order_by(ActionPlanResult.created_at.desc()).all()
    return [_action_to_dict(r) for r in results]


def compute_period_comparison(db: Session, teacher_id: str) -> dict:
    """Compare scores before vs after executed action plans."""
    results = db.query(ActionPlanResult).filter(
        ActionPlanResult.teacher_id == teacher_id,
        ActionPlanResult.status.in_(["realizado", "parcial"]),
        ActionPlanResult.score_before.isnot(None),
        ActionPlanResult.score_after.isnot(None),
    ).all()

    if not results:
        return {"comparisons": [], "avg_delta": 0, "completion_rate": None}

    total = db.query(ActionPlanResult).filter(ActionPlanResult.teacher_id == teacher_id).count()
    completed = len(results)

    comparisons = [
        {
            "action_text": r.action_text,
            "score_before": r.score_before,
            "score_after": r.score_after,
            "delta": r.delta_score,
            "status": r.status,
        }
        for r in results
    ]

    deltas = [r.delta_score for r in results if r.delta_score is not None]
    avg_delta = round(sum(deltas) / len(deltas), 1) if deltas else 0

    return {
        "comparisons": comparisons,
        "avg_delta": avg_delta,
        "completion_rate": round(completed / total * 100) if total else 0,
    }


def _action_to_dict(r: ActionPlanResult) -> dict:
    return {
        "id": r.id,
        "observation_id": r.observation_id,
        "teacher_id": r.teacher_id,
        "action_text": r.action_text,
        "action_type": r.action_type,
        "deadline": r.deadline.isoformat() if r.deadline else None,
        "responsible": r.responsible,
        "status": r.status,
        "result_notes": r.result_notes,
        "score_before": r.score_before,
        "score_after": r.score_after,
        "delta_score": r.delta_score,
        "created_at": r.created_at.isoformat(),
    }
