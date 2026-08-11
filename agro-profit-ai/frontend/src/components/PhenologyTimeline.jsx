import { formatNumber } from "../utils/format.js";

export default function PhenologyTimeline({ phenology }) {
  if (!phenology?.available) {
    return (
      <div className="empty-state">
        Fenologia indisponível{phenology?.reason ? ` — ${phenology.reason}` : ""}. Cadastre a data de plantio do talhão.
      </div>
    );
  }

  const { timeline, accumulated_gdd, cycle_gdd, cycle_progress_pct } = phenology;

  return (
    <div>
      <div className="pheno-progress-track">
        <div className="pheno-progress-fill" style={{ width: `${Math.min(100, cycle_progress_pct)}%` }} />
      </div>
      <p className="muted" style={{ fontSize: 12, marginTop: 6 }}>
        {formatNumber(accumulated_gdd, 0)} de {formatNumber(cycle_gdd, 0)} graus-dia acumulados ·{" "}
        {formatNumber(cycle_progress_pct, 0)}% do ciclo · {phenology.days_since_planting} dias desde o plantio
      </p>

      <div className="pheno-stages">
        {timeline.map((stage) => (
          <div
            key={stage.name}
            className={`pheno-stage${stage.is_current ? " current" : ""}${stage.reached ? " reached" : ""}`}
          >
            <div className="pheno-stage-dot" />
            <div className="pheno-stage-label">{stage.label}</div>
            <div className="pheno-stage-meta muted">
              {stage.gdd_start} GDD · Kc {stage.kc}
              {stage.water_sensitivity >= 0.8 && <span className="badge badge-high" style={{ marginLeft: 6 }}>crítico água</span>}
            </div>
            {stage.started_on && <div className="pheno-stage-meta muted">início {stage.started_on}</div>}
            {stage.stats && (
              <div className="pheno-stage-meta muted">
                {formatNumber(stage.stats.rain_mm, 0)} mm chuva · {stage.stats.days} dias
                {stage.stats.heat_stress_days > 0 && ` · ${stage.stats.heat_stress_days}d calor`}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
