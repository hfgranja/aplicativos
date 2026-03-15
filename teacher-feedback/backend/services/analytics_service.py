from typing import List
from services.llm_service import compute_section_scores, compute_ef1_scores, SECTION_NAMES

EF1_DOMAIN_NAMES = {
    "dc": "Domínio de Conteúdo",
    "es": "Engajamento dos Estudantes",
    "me": "Metodologias e Estratégias",
    "md": "Material Didático",
    "gs": "Gestão de Sala",
    "mc": "Manejo de Conflitos",
}


def compute_evolution(observations: List) -> dict:
    """Returns time-series data for evolution charts (PEC + EF I)."""
    series = []
    has_ef1 = False
    for obs in sorted(observations, key=lambda o: o.observed_at):
        scores = compute_section_scores(obs)
        ef1 = compute_ef1_scores(obs)
        row = {
            "id": obs.id,
            "date": obs.observed_at.strftime("%d/%m/%Y"),
            "observed_at": obs.observed_at.isoformat(),
            **{k: v for k, v in scores.items()},
        }
        if any(v > 0 for v in ef1.values()):
            has_ef1 = True
            for k, v in ef1.items():
                row[f"ef1_{k}"] = v
        series.append(row)

    # Compute trend for each section (PEC)
    trends = {}
    all_keys = ["s1", "s2", "s3", "s4", "s5", "total"]
    if has_ef1:
        all_keys += [f"ef1_{d}" for d in EF1_DOMAIN_NAMES.keys()]

    if len(series) >= 2:
        for sec in all_keys:
            vals = [s.get(sec, 0) for s in series]
            delta = vals[-1] - vals[0]
            avg_delta = delta / (len(vals) - 1) if len(vals) > 1 else 0
            if avg_delta > 5:
                trend = "improving"
            elif avg_delta < -5:
                trend = "declining"
            else:
                trend = "stable"
            trends[sec] = {"trend": trend, "delta": round(delta), "avg_delta": round(avg_delta, 1)}

    return {
        "series": series,
        "trends": trends,
        "section_names": SECTION_NAMES,
        "ef1_domain_names": EF1_DOMAIN_NAMES,
        "has_ef1": has_ef1,
    }


def compute_comparative(obs1, obs2) -> dict:
    """Returns comparison data between two observations."""
    scores1 = compute_section_scores(obs1)
    scores2 = compute_section_scores(obs2)

    diff = {sec: scores2[sec] - scores1[sec] for sec in ["s1", "s2", "s3", "s4", "s5", "total"]}

    radar = [
        {
            "section": SECTION_NAMES[sec],
            "key": sec,
            "obs1": scores1[sec],
            "obs2": scores2[sec],
        }
        for sec in ["s1", "s2", "s3", "s4", "s5"]
    ]

    return {
        "obs1": {"id": obs1.id, "date": obs1.observed_at.strftime("%d/%m/%Y"), "scores": scores1},
        "obs2": {"id": obs2.id, "date": obs2.observed_at.strftime("%d/%m/%Y"), "scores": scores2},
        "diff": diff,
        "radar": radar,
        "section_names": SECTION_NAMES,
    }
