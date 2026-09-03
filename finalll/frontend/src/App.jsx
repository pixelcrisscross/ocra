import { useRef, useEffect } from 'react'
import { useState } from 'react'
import { askOrca, API_BASE } from './api.js'

let initialConversationId = null

function formatCondition(label, point) {
  if (!point || point.value === null || point.value === undefined) return null
  const unit = point.unit ? ` ${point.unit}` : ''
  return { label, value: `${point.value}${unit}` }
}

function ConditionsPanel({ title, data }) {
  const rows = Object.entries(data || {})
    .map(([key, point]) => formatCondition(key.replaceAll('_', ' '), point))
    .filter(Boolean)

  if (rows.length === 0) return null
  return (
    <div className="conditions">
      <h5>{title}</h5>
      <ul>
        {rows.map((r) => (
          <li key={r.label}>
            <span>{r.label}</span>
            <strong>{r.value}</strong>
          </li>
        ))}
      </ul>
    </div>
  )
}

function AssistantBlock({ item }) {
  const { answer, conversationId } = item
  const [showDetails, setShowDetails] = useState(false)

  const hasDetails =
    (answer.observations && answer.observations.length) ||
    (answer.recommendations && answer.recommendations.length) ||
    (item.sources && item.sources.length) ||
    (item.data_quality && Object.keys(item.data_quality).length) ||
    (item.ocean && Object.keys(item.ocean).length) ||
    (item.weather && Object.keys(item.weather).length) ||
    (item.hazards && item.hazards.length)

  return (
    <div className="msg assistant">
      <div className="bubble">
        <p className="summary">{answer.summary}</p>
        {hasDetails && (
          <button className="toggle" onClick={() => setShowDetails((s) => !s)}>
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
        )}
        {showDetails && (
          <div className="details">
            {answer.observations && answer.observations.length > 0 && (
              <div>
                <h4>Observations</h4>
                <ul>{answer.observations.map((o, i) => <li key={i}>{o}</li>)}</ul>
              </div>
            )}
            {answer.recommendations && answer.recommendations.length > 0 && (
              <div>
                <h4>Recommendations</h4>
                <ul>{answer.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
              </div>
            )}
            <ConditionsPanel title="Ocean" data={item.ocean} />
            <ConditionsPanel title="Weather" data={item.weather} />
            {item.hazards && item.hazards.length > 0 && (
              <div>
                <h4>Hazards ({item.hazards.length})</h4>
                <ul>{item.hazards.map((h, i) => <li key={i}>{h.name} — {h.status}</li>)}</ul>
              </div>
            )}
            {item.data_quality && (
              <div>
                <h4>Data quality</h4>
                <p>Completeness: {item.data_quality.completeness_percent ?? 'n/a'}% · Sources: {item.data_quality.source_count ?? 'n/a'}</p>
                {item.data_quality.missing && item.data_quality.missing.length > 0 && (
                  <p className="muted">Missing: {item.data_quality.missing.join(', ')}</p>
                )}
              </div>
            )}
            {item.sources && item.sources.length > 0 && (
              <div>
                <h4>Sources</h4>
                <ul>
                  {item.sources.map((s, i) => (
                    <li key={i}>
                      {s.url && (<a href={s.url} target="_blank" rel="noreferrer">{s.name || s.url}</a>)}
                      {!s.url && s.name}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        <span className="meta">session: {conversationId}</span>
      </div>
    </div>
  )
}

function UserBlock({ item }) {
  return (
    <div className="msg user">
      <div className="bubble">{item.text}</div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [conversationId, setConversationId] = useState(initialConversationId)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setError(null)
    setMessages((m) => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      const data = await askOrca(text, conversationId)
      setConversationId((id) => {
        const next = data.conversation_id || id
        initialConversationId = next
        return next
      })
      const block = { role: 'assistant', conversationId: data.conversation_id, answer: data.answer, ocean: data.ocean, weather: data.weather, hazards: data.hazards, sources: data.sources, data_quality: data.data_quality }
      setMessages((m) => [...m, block])
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="app">
      <header>
        <h1>ORCA Marine Intelligence</h1>
        <p className="meta">Conversational marine decision-support. Backend: <code>{API_BASE}</code></p>
      </header>

      <main className="chat">
        {messages.length === 0 && (
          <div className="empty">
            <p>Ask about ocean conditions, weather, fishing zones, hazards or safe route planning.</p>
            <p className="muted">e.g. "What are the current sea conditions near Visakhapatnam?"</p>
          </div>
        )}
        {messages.map((m, i) =>
          m.role === 'user' ? <UserBlock key={i} item={m} /> : <AssistantBlock key={i} item={m} />
        )}
        {loading && <div className="msg assistant"><div className="bubble typing">Thinking…</div></div>}
        {error && <div className="msg assistant"><div className="bubble error">{error}</div></div>}
        <div ref={endRef} />
      </main>

      <footer>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask about marine conditions…"
          rows={2}
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !input.trim()}>Send</button>
      </footer>
    </div>
  )
}
