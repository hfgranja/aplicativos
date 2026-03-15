import { useState } from 'react'
import { scoreColor } from '../theme.js'

export default function ScoreCard({ result }) {
  const [expanded, setExpanded] = useState(false)
  const { name, icon, score, color, issues, suggestions, detail } = result
  const sColor = scoreColor(score)

  return (
    <div
      onClick={() => setExpanded(e => !e)}
      style={{
        background: '#13131A',
        border: `1px solid ${expanded ? color + '50' : 'rgba(255,255,255,0.07)'}`,
        borderRadius: 14,
        padding: '16px 18px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = color + '40' }}
      onMouseLeave={e => {
        if (!expanded) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)'
      }}
    >
      {/* Colored left strip */}
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
        background: color, borderRadius: '14px 0 0 14px',
        opacity: 0.8,
      }} />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginLeft: 8 }}>
        <span style={{ fontSize: 20 }}>{icon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#E8E8F0', marginBottom: 2 }}>
            {name}
          </div>
          <div style={{ fontSize: 10, color: 'rgba(232,232,240,0.35)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {detail}
          </div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{
            fontSize: 22, fontWeight: 700, color: sColor,
            fontFamily: 'JetBrains Mono, monospace',
            lineHeight: 1,
          }}>
            {score}
          </div>
          <div style={{ fontSize: 9, color: 'rgba(232,232,240,0.3)', marginTop: 2 }}>/100</div>
        </div>
      </div>

      {/* Mini score bar */}
      <div style={{
        height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2,
        marginTop: 12, marginLeft: 8, overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${score}%`,
          background: `linear-gradient(90deg, ${color}, ${sColor})`,
          borderRadius: 2, transition: 'width 0.8s ease',
        }} />
      </div>

      {/* Expanded details */}
      {expanded && (
        <div style={{ marginTop: 16, marginLeft: 8 }}>
          {issues.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,77,109,0.8)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>
                Problemas Encontrados
              </div>
              {issues.map((issue, i) => (
                <div key={i} style={{
                  fontSize: 12, color: 'rgba(232,232,240,0.7)', marginBottom: 4,
                  paddingLeft: 10, borderLeft: '2px solid rgba(255,77,109,0.4)',
                  lineHeight: 1.5,
                }}>
                  {issue}
                </div>
              ))}
            </div>
          )}
          {suggestions.length > 0 && (
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(0,200,150,0.8)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>
                Sugestões
              </div>
              {suggestions.map((s, i) => (
                <div key={i} style={{
                  fontSize: 12, color: 'rgba(232,232,240,0.7)', marginBottom: 4,
                  paddingLeft: 10, borderLeft: '2px solid rgba(0,200,150,0.4)',
                  lineHeight: 1.5,
                }}>
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div style={{
        position: 'absolute', bottom: 8, right: 12,
        fontSize: 10, color: 'rgba(255,255,255,0.2)',
      }}>
        {expanded ? '▲' : '▼'}
      </div>
    </div>
  )
}
