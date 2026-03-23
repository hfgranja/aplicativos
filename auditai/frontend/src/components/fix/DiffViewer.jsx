export default function DiffViewer({ before, after, diff }) {
  if (diff) {
    return (
      <div style={{ fontFamily: 'monospace', fontSize: 13, overflowX: 'auto' }}>
        {diff.split('\n').map((line, i) => {
          let bg = 'transparent', color = '#e2e8f0'
          if (line.startsWith('+')) { bg = '#052e16'; color = '#4ade80' }
          else if (line.startsWith('-')) { bg = '#450a0a'; color = '#f87171' }
          else if (line.startsWith('@@')) { color = '#60a5fa' }
          return (
            <div key={i} style={{ background: bg, color, padding: '1px 8px', whiteSpace: 'pre' }}>
              {line}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
      <div>
        <div style={{ fontSize: 11, color: '#f87171', marginBottom: 4 }}>Before</div>
        <pre style={{ background: '#450a0a', padding: 12, borderRadius: 6, fontSize: 12,
          overflow: 'auto', color: '#fca5a5', border: '1px solid #991b1b' }}>
          {before || '(no code)'}
        </pre>
      </div>
      <div>
        <div style={{ fontSize: 11, color: '#4ade80', marginBottom: 4 }}>After</div>
        <pre style={{ background: '#052e16', padding: 12, borderRadius: 6, fontSize: 12,
          overflow: 'auto', color: '#86efac', border: '1px solid #166534' }}>
          {after || '(no fix generated)'}
        </pre>
      </div>
    </div>
  )
}
