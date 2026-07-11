import { useState, useEffect } from 'react'
import { Tag, Plus, X, Eye, EyeOff, CheckCircle, Trash2, Sparkles, Target } from 'lucide-react'
import api from '../api/client'
import { Card, GhostButton, Skeleton, EmptyState, SectionHeader } from '../components/ui'

const BENCHMARK_OPTIONS = [
  { value: 'sector_median', label: 'Sector Median' },
  { value: 'upper_quartile', label: 'Upper Quartile (Q3)' },
  { value: 'absolute', label: 'Absolute Threshold' },
  { value: 'risk_adjusted', label: 'Risk Adjusted' },
]
const ADJUSTMENT_OPTIONS = [
  { value: 'none', label: 'None' },
  { value: 'z_score', label: 'Z-Score' },
  { value: 'percentile', label: 'Percentile' },
]

function PreviewChart({ preview }) {
  if (!preview) return null
  const total = (preview.positive_count || 0) + (preview.negative_count || 0)
  const posPct = total > 0 ? ((preview.positive_count / total) * 100).toFixed(1) : 0
  const negPct = total > 0 ? ((preview.negative_count / total) * 100).toFixed(1) : 0

  return (
    <div style={{ background: 'var(--bg)', borderRadius: 'var(--radius-md)', padding: '12px 16px', marginTop: 14 }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 10 }}>
        Distribution Preview
      </div>
      {preview.imbalance_warning && (
        <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 'var(--radius-md)', padding: '6px 12px', color: 'var(--warning)', fontSize: 12, marginBottom: 10 }}>
          ⚠ Imbalance warning — Positive/negative ratio may be skewed
        </div>
      )}
      <div style={{ height: 20, borderRadius: 4, overflow: 'hidden', display: 'flex' }}>
        <div style={{
          width: `${posPct}%`, background: 'var(--success)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, color: '#fff', fontWeight: 700, minWidth: 28,
        }}>
          {posPct}%
        </div>
        <div style={{
          flex: 1, background: 'var(--danger)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, color: '#fff', fontWeight: 700, minWidth: 28,
        }}>
          {negPct}%
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 12 }}>
        <span style={{ color: 'var(--success)' }}>Positive: <strong>{preview.positive_count}</strong></span>
        <span style={{ color: 'var(--danger)' }}>Negative: <strong>{preview.negative_count}</strong></span>
        <span style={{ color: 'var(--text-3)' }}>Total: <strong>{total}</strong></span>
      </div>
    </div>
  )
}

const labHero = { border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))', padding: 24, marginBottom: 24 }
const heroKicker = { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 }
const heroTitle = { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2rem, 5vw, 3.25rem)', lineHeight: 1, fontWeight: 900, maxWidth: 820 }
const heroSub = { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 760 }
const heroBadge = { display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 16, background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-strong)', borderRadius: 999, padding: '6px 10px', color: 'var(--text-2)', fontSize: 12, fontWeight: 800 }
const inputS = {
  width: '100%', boxSizing: 'border-box',
  background: 'var(--surface-1)', border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)', color: 'var(--text-1)',
  padding: '8px 12px', fontSize: 13, outline: 'none',
}

export default function LabelingLabPage() {
  const [defs, setDefs] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [msg, setMsg] = useState('')
  const [form, setForm] = useState({
    name: '', sector_benchmark_type: 'sector_median', horizon_months: 12,
    success_threshold: 0.55, sector_adjustment_mode: 'none', threshold_rule: '',
  })
  const [previews, setPreviews] = useState({})
  const [previewLoading, setPreviewLoading] = useState({})

  const fetchDefs = () => api.get('/labeling/definitions').then(({ data }) => setDefs(data)).catch(() => {})
  useEffect(() => { fetchDefs() }, [])

  const handleCreate = async () => {
    try {
      await api.post('/labeling/definitions', { ...form, horizon_months: parseInt(form.horizon_months), success_threshold: parseFloat(form.success_threshold) })
      setMsg('Definition created.'); setShowCreate(false); fetchDefs()
    } catch (e) { setMsg(e.response?.data?.detail || 'An error occurred.') }
  }
  const handleActivate = async (id) => {
    try { await api.post(`/labeling/definitions/${id}/activate`); setMsg('Definition activated.'); fetchDefs() }
    catch (e) { setMsg(e.response?.data?.detail || 'An error occurred.') }
  }
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this definition?')) return
    try { await api.delete(`/labeling/definitions/${id}`); setMsg('Definition deleted.'); fetchDefs() }
    catch (e) { setMsg(e.response?.data?.detail || 'An error occurred.') }
  }
  const handlePreview = async (id) => {
    if (previews[id]) { setPreviews(p => { const n = { ...p }; delete n[id]; return n }); return }
    setPreviewLoading(p => ({ ...p, [id]: true }))
    try { const { data } = await api.post(`/labeling/definitions/${id}/preview`); setPreviews(p => ({ ...p, [id]: data })) }
    catch (e) { setMsg(e.response?.data?.detail || 'Preview failed.') }
    finally { setPreviewLoading(p => ({ ...p, [id]: false })) }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <section style={labHero}>
        <div style={heroKicker}><Sparkles size={15} /> Label Governance</div>
        <h1 style={heroTitle}>Define targets before judging models.</h1>
        <p style={heroSub}>Create, preview, and activate label strategies with visible class balance before validation.</p>
        <span style={heroBadge}><Target size={13} /> Label strategy workflow</span>
      </section>

      {msg && (
        <div style={{ background: 'rgba(14,165,233,0.08)', border: '1px solid rgba(14,165,233,0.25)', borderRadius: 'var(--radius-md)', padding: '10px 14px', color: 'var(--primary)', fontSize: 13, marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <span>{msg}</span>
          <button onClick={() => setMsg('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', padding: 0 }}><X size={14} /></button>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <GhostButton onClick={() => setShowCreate(!showCreate)} style={{ gap: 6 }}>
          {showCreate ? <><X size={14} /> Cancel</> : <><Plus size={14} /> New Definition</>}
        </GhostButton>
      </div>

      {showCreate && (
        <Card style={{ padding: '1.25rem', marginBottom: 16, borderColor: 'var(--primary-muted)' }}>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-1)', marginBottom: 14 }}>New Label Definition</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {[['name', 'Definition Name', 'text', 'e.g. Sector Median 12M'], ['horizon_months', 'Horizon (months)', 'number'], ['success_threshold', 'Success Threshold (0–1)', 'number'], ['threshold_rule', 'Threshold Rule (optional)', 'text', 'e.g. score > 65']].map(([f, lbl, type, ph]) => (
              <div key={f}>
                <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 5 }}>{lbl}</label>
                <input style={inputS} type={type || 'text'} placeholder={ph} step={type === 'number' && f.includes('threshold') ? '0.01' : undefined}
                  value={form[f]} onChange={e => setForm(p => ({ ...p, [f]: e.target.value }))} />
              </div>
            ))}
            <div>
              <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 5 }}>Benchmark Type</label>
              <select style={inputS} value={form.sector_benchmark_type} onChange={e => setForm(p => ({ ...p, sector_benchmark_type: e.target.value }))}>
                {BENCHMARK_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 5 }}>Sector Adjustment</label>
              <select style={inputS} value={form.sector_adjustment_mode} onChange={e => setForm(p => ({ ...p, sector_adjustment_mode: e.target.value }))}>
                {ADJUSTMENT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>
          <button onClick={handleCreate} style={{ marginTop: 14, background: 'var(--primary)', border: 'none', borderRadius: 'var(--radius-md)', color: '#fff', padding: '9px 20px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
            Create
          </button>
        </Card>
      )}

      <SectionHeader title={`Current Definitions — ${defs.length}`} icon={<Tag size={15} />} style={{ marginBottom: 12 }} />

      {defs.length === 0 ? (
        <EmptyState icon={<Tag size={28} />} title="No definitions yet" description="Create a new label definition to get started." />
      ) : defs.map(d => (
        <Card key={d.id} style={{ padding: '1.1rem 1.25rem', marginBottom: 12, borderColor: d.is_active ? 'rgba(16,185,129,0.3)' : 'var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-1)' }}>{d.name}</span>
                <span style={{
                  background: d.is_active ? 'rgba(16,185,129,0.1)' : 'var(--surface-3)',
                  color: d.is_active ? 'var(--success)' : 'var(--text-3)',
                  border: `1px solid ${d.is_active ? 'rgba(16,185,129,0.25)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius-2xl)', padding: '2px 10px', fontSize: 11, fontWeight: 600,
                }}>
                  {d.is_active ? 'active' : 'inactive'}
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <span>{BENCHMARK_OPTIONS.find(o => o.value === d.sector_benchmark_type)?.label || d.sector_benchmark_type}</span>
                <span>· {d.horizon_months} months</span>
                <span>· {(d.success_threshold * 100).toFixed(0)}% threshold</span>
                {d.sector_adjustment_mode && d.sector_adjustment_mode !== 'none' && <span>· {d.sector_adjustment_mode.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0, flexWrap: 'wrap' }}>
              <GhostButton onClick={() => handlePreview(d.id)} disabled={previewLoading[d.id]} style={{ gap: 5, fontSize: 12, padding: '5px 12px' }}>
                {previewLoading[d.id] ? '...' : previews[d.id] ? <><EyeOff size={13} /> Hide</> : <><Eye size={13} /> Preview</>}
              </GhostButton>
              {!d.is_active && <GhostButton onClick={() => handleActivate(d.id)} style={{ gap: 5, fontSize: 12, padding: '5px 12px', color: 'var(--success)', borderColor: 'rgba(16,185,129,0.3)' }}>
                <CheckCircle size={13} /> Activate
              </GhostButton>}
              {!d.is_active && <GhostButton onClick={() => handleDelete(d.id)} style={{ gap: 5, fontSize: 12, padding: '5px 12px', color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.3)' }}>
                <Trash2 size={13} /> Delete
              </GhostButton>}
            </div>
          </div>
          {previews[d.id] && <PreviewChart preview={previews[d.id]} />}
        </Card>
      ))}

      <footer style={{ marginTop: 28, borderTop: '1px solid var(--border)', paddingTop: 12, color: 'var(--text-3)', fontSize: 11 }}>
        Experimental ranking signal — research support only, NOT investment advice. Do not use for buy/sell/hold decisions.
      </footer>
    </div>
  )
}
