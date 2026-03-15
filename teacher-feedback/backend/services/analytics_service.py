from typing import List
from services.llm_service import compute_section_scores, SECTION_NAMES


def compute_evolution(observations: List) -> dict:
    """Returns time-series data for evolution charts."""
    series = []
    for obs in sorted(observations, key=lambda o: o.observed_at):
        scores = compute_section_scores(obs)
        series.append({
            "id": obs.id,
            "date": obs.observed_at.strftime("%d/%m/%Y"),
            "observed_at": obs.observed_at.isoformat(),
            **{k: v for k, v in scores.items()},
        })

    # Compute trend for each section
    trends = {}
    if len(series) >= 2:
        for sec in ["s1", "s2", "s3", "s4", "s5", "total"]:
            vals = [s[sec] for s in series]
            delta = vals[-1] - vals[0]
            if len(vals) > 1:
                avg_delta = delta / (len(vals) - 1)
            else:
                avg_delta = 0
            if avg_delta > 5:
                trend = "improving"
            elif avg_delta < -5:
                trend = "declining"
            else:
                trend = "stable"
            trends[sec] = {"trend": trend, "delta": round(delta), "avg_delta": round(avg_delta, 1)}

    return {"series": series, "trends": trends, "section_names": SECTION_NAMES}


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
