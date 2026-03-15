import { RATING_LABELS, RATING_COLORS, C } from '../../colors'

const RATINGS = ['nao_observado', 'insuficiente', 'adequado', 'muito_bom']

export function RatingButton({ field, value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {RATINGS.map(r => {
        const selected = value === r
        const color = RATING_COLORS[r]
        return (
          <button
            key={r}
            type="button"
            onClick={() => onChange(field, r)}
            style={{
              padding: '5px 12px', borderRadius: 6, fontSize: 11, fontWeight: 600,
              cursor: 'pointer', fontFamily: 'JetBrains Mono',
              background: selected ? color + '33' : C.surface3,
              border: `1.5px solid ${selected ? color : C.border}`,
              color: selected ? color : C.textMuted,
              transition: 'all 0.15s',
            }}
          >
            {RATING_LABELS[r]}
          </button>
        )
      })}
    </div>
  )
}

export function CriteriaRow({ label, field, value, onChange }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'center',
      padding: '14px 0', borderBottom: `1px solid ${C.border}`,
    }}>
      <span style={{ fontSize: 13, color: C.text, lineHeight: 1.5 }}>{label}</span>
      <RatingButton field={field} value={value} onChange={onChange} />
    </div>
  )
}
