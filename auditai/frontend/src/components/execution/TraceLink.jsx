/**
 * TraceLink — renders a "View Trace" link for an engine test run.
 * Visible only when trace_id is present in the run's evidence and
 * VITE_TRACE_UI_URL is configured.
 */
const TRACE_UI_URL = import.meta.env.VITE_TRACE_UI_URL || ''

const s = {
  link: { fontSize: 11, color: '#38bdf8', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 },
  dot: { width: 6, height: 6, borderRadius: '50%', background: '#38bdf8', display: 'inline-block' },
}

export default function TraceLink({ evidence }) {
  const traceId = evidence?.trace_id
  if (!traceId || !TRACE_UI_URL) return null

  const url = `${TRACE_UI_URL.replace(/\/$/, '')}/trace/${traceId}`

  return (
    <a href={url} target="_blank" rel="noopener noreferrer" style={s.link} title={`Trace ID: ${traceId}`}>
      <span style={s.dot} />
      View Trace
    </a>
  )
}
