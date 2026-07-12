import { useCallback, useEffect, useState } from 'react'
import { MessageSquareWarning, RefreshCw, Send } from 'lucide-react'
import api from '../api/client'
import { Card, EmptyState, GhostButton, SectionHeader } from './ui'

const VERDICTS = [
  ['agree', 'Agree'],
  ['disagree', 'Disagree'],
  ['abstain', 'Abstain'],
]
const REASONS = [
  ['evidence_quality', 'Evidence quality'],
  ['data_gap', 'Data gap'],
  ['methodology', 'Methodology'],
  ['model_instability', 'Model instability'],
  ['other', 'Other'],
]
const BOUNDARY = 'Records disagreement for research; never a score input.'

const inputStyle = {
  width: '100%', boxSizing: 'border-box', background: 'var(--surface-1)',
  border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)',
  color: 'var(--text-1)', padding: '8px 10px', fontSize: 13, fontFamily: 'inherit',
}

function reasonSummary(counts = {}) {
  const labels = Object.fromEntries(REASONS)
  return REASONS
    .filter(([key]) => Number(counts[key]) > 0)
    .map(([key]) => `${labels[key]} ${counts[key]}`)
    .join(' · ') || '—'
}

export default function DissentLedger() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [form, setForm] = useState({
    ticker: '', year: 2025, verdict: 'abstain', reason_type: 'data_gap', note: '',
  })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/analyst-verdicts/aggregate')
      setRows(data.rows || [])
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Dissent ledger could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const submit = async () => {
    if (!form.ticker.trim()) {
      setMessage('Ticker is required.')
      return
    }
    setSaving(true)
    setMessage('')
    try {
      await api.post('/analyst-verdicts', {
        ...form,
        ticker: form.ticker.trim().toUpperCase(),
        year: Number(form.year),
        note: form.note.trim() || null,
      })
      setForm(current => ({ ...current, ticker: '', note: '' }))
      setMessage('Verdict appended to the research ledger.')
      await load()
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Authenticated verdict write failed.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card style={{ marginTop: 24, padding: '1.1rem 1.25rem' }}>
      <SectionHeader title="Analyst dissent ledger" icon={<MessageSquareWarning size={15} />} />
      <div style={{ margin: '10px 0 16px', padding: '10px 12px', borderRadius: 'var(--radius-md)', background: 'rgba(244,176,74,0.08)', border: '1px solid rgba(244,176,74,0.24)' }}>
        <strong style={{ color: 'var(--primary-hover)', fontSize: 13 }}>{BOUNDARY}</strong>
        <div style={{ color: 'var(--text-2)', fontSize: 12, lineHeight: 1.55, marginTop: 4 }}>
          Counts are descriptive ledger records, not consensus, a recommendation, or a crowd signal. Research workflow only; not investment advice.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10, alignItems: 'end' }}>
        <label style={{ color: 'var(--text-2)', fontSize: 11 }}>
          Ticker
          <input style={{ ...inputStyle, marginTop: 5 }} value={form.ticker} maxLength={20} placeholder="ASELS" onChange={event => setForm(current => ({ ...current, ticker: event.target.value.toUpperCase() }))} />
        </label>
        <label style={{ color: 'var(--text-2)', fontSize: 11 }}>
          Evidence year
          <input style={{ ...inputStyle, marginTop: 5 }} type="number" min="2000" max="2100" value={form.year} onChange={event => setForm(current => ({ ...current, year: event.target.value }))} />
        </label>
        <label style={{ color: 'var(--text-2)', fontSize: 11 }}>
          Verdict
          <select style={{ ...inputStyle, marginTop: 5 }} value={form.verdict} onChange={event => setForm(current => ({ ...current, verdict: event.target.value }))}>
            {VERDICTS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label style={{ color: 'var(--text-2)', fontSize: 11 }}>
          Reason
          <select style={{ ...inputStyle, marginTop: 5 }} value={form.reason_type} onChange={event => setForm(current => ({ ...current, reason_type: event.target.value }))}>
            {REASONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 10, marginTop: 10, alignItems: 'end' }}>
        <label style={{ color: 'var(--text-2)', fontSize: 11 }}>
          Note (optional, max 2,000 characters)
          <textarea style={{ ...inputStyle, marginTop: 5, resize: 'vertical', minHeight: 72 }} maxLength={2000} value={form.note} onChange={event => setForm(current => ({ ...current, note: event.target.value }))} />
        </label>
        <button onClick={submit} disabled={saving} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: saving ? 'var(--surface-3)' : 'var(--primary)', color: saving ? 'var(--text-3)' : '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 16px', fontSize: 13, fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer' }}>
          <Send size={14} /> {saving ? 'Appending…' : 'Append verdict'}
        </button>
      </div>

      {message && <div style={{ color: 'var(--text-2)', fontSize: 12, marginTop: 10 }}>{message}</div>}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '20px 0 8px' }}>
        <strong style={{ color: 'var(--text-1)', fontSize: 13 }}>Descriptive counts</strong>
        <GhostButton onClick={load} disabled={loading} style={{ gap: 5, fontSize: 11, padding: '5px 10px' }}>
          <RefreshCw size={12} /> Refresh
        </GhostButton>
      </div>
      {loading ? (
        <div style={{ color: 'var(--text-3)', fontSize: 12 }}>Loading ledger…</div>
      ) : rows.length === 0 ? (
        <EmptyState icon={<MessageSquareWarning size={24} />} title="No verdicts recorded" description="Authenticated analysts can append the first research disagreement above." />
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead><tr>{['Ticker / year', 'Agree', 'Disagree', 'Abstain', 'Total', 'Reasons'].map(label => <th key={label} style={{ textAlign: 'left', color: 'var(--text-3)', padding: '7px 8px', background: 'var(--surface-1)' }}>{label}</th>)}</tr></thead>
            <tbody>{rows.map(row => (
              <tr key={`${row.ticker}-${row.year}`}>
                <td style={{ color: 'var(--text-1)', fontWeight: 700, padding: '8px', borderTop: '1px solid var(--border)' }}>{row.ticker} · {row.year}</td>
                <td style={{ color: 'var(--text-2)', padding: '8px', borderTop: '1px solid var(--border)' }}>{row.verdict_counts.agree}</td>
                <td style={{ color: 'var(--text-2)', padding: '8px', borderTop: '1px solid var(--border)' }}>{row.verdict_counts.disagree}</td>
                <td style={{ color: 'var(--text-2)', padding: '8px', borderTop: '1px solid var(--border)' }}>{row.verdict_counts.abstain}</td>
                <td style={{ color: 'var(--text-1)', fontWeight: 700, padding: '8px', borderTop: '1px solid var(--border)' }}>{row.verdict_counts.total}</td>
                <td style={{ color: 'var(--text-3)', padding: '8px', borderTop: '1px solid var(--border)' }}>{reasonSummary(row.reason_counts)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </Card>
  )
}
