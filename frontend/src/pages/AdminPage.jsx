import { useState, useEffect } from 'react'
import { Box, Users, ClipboardList, Plus, X, CheckCircle, Archive, Trash2, FlaskConical, ChevronDown, ChevronUp, Settings, ShieldCheck, Sparkles } from 'lucide-react'
import api from '../api/client'
import { Card, Chip, GhostButton, SectionHeader, Skeleton, EmptyState } from '../components/ui'

const ACTION_ICONS = {
  model_activated: '✅', model_created: '🆕', model_archived: '📦', model_updated: '✏️',
  model_deleted: '🗑️', label_created: '🏷️', label_activated: '✅', label_deleted: '🗑️',
  validation_run_created: '🔬', user_role_changed: '👤', ingestion_started: '📥', default: '📋',
}

function statusChipStyle(status) {
  if (status === 'active') return { background: 'rgba(16,185,129,0.12)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.25)' }
  if (status === 'archived') return { background: 'var(--surface-1)', color: 'var(--text-3)', border: '1px solid var(--border)' }
  return { background: 'rgba(14,165,233,0.1)', color: 'var(--primary)', border: '1px solid rgba(14,165,233,0.25)' }
}

function ModelCard({ model, onActivate, onArchive, onDelete, onRunValidation }) {
  const [showDetails, setShowDetails] = useState(false)

  let metrics = null
  if (model.validation_summary_json) {
    try { metrics = JSON.parse(model.validation_summary_json) } catch {}
  }

  return (
    <Card style={{ padding: '1.1rem 1.25rem', marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-1)' }}>{model.model_name}</span>
            <span style={{ ...statusChipStyle(model.status || 'draft'), borderRadius: 'var(--radius-2xl)', padding: '2px 10px', fontSize: 11, fontWeight: 600 }}>
              {model.status || 'draft'}
            </span>
            {model.model_type === 'logistic' && (
              <span style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--info)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 'var(--radius-2xl)', padding: '2px 10px', fontSize: 11, fontWeight: 600 }}>
                LR
              </span>
            )}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-3)', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <span>v{model.version}</span>
            {model.evaluation_horizon && <span>· {model.evaluation_horizon}</span>}
            {model.label_strategy && <span>· {model.label_strategy}</span>}
            {model.feature_set_version && <span>· {model.feature_set_version}</span>}
          </div>
          {metrics && (
            <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
              {metrics.accuracy != null && (
                <span style={{ background: 'var(--surface-3)', borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 11, color: 'var(--text-2)' }}>
                  ACC {(metrics.accuracy * 100).toFixed(1)}%
                </span>
              )}
              {metrics.f1 != null && (
                <span style={{ background: 'var(--surface-3)', borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 11, color: 'var(--text-2)' }}>
                  F1 {metrics.f1.toFixed(3)}
                </span>
              )}
              {metrics.roc_auc != null && (
                <span style={{ background: 'var(--surface-3)', borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 11, color: 'var(--text-2)' }}>
                  AUC {metrics.roc_auc.toFixed(3)}
                </span>
              )}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', flexShrink: 0 }}>
          {model.status !== 'active' && (
            <GhostButton onClick={() => onActivate(model.id)} style={{ gap: 5, fontSize: 12, padding: '5px 12px', color: 'var(--success)', borderColor: 'rgba(16,185,129,0.3)' }}>
              <CheckCircle size={13} /> Activate
            </GhostButton>
          )}
          {model.status !== 'archived' && (
            <GhostButton onClick={() => onArchive(model.id)} style={{ gap: 5, fontSize: 12, padding: '5px 12px' }}>
              <Archive size={13} /> Archive
            </GhostButton>
          )}
          <GhostButton onClick={() => onRunValidation(model.id)} style={{ gap: 5, fontSize: 12, padding: '5px 12px' }}>
              <FlaskConical size={13} /> Validate
          </GhostButton>
          {model.status === 'archived' && (
            <GhostButton onClick={() => onDelete(model.id)} style={{ gap: 5, fontSize: 12, padding: '5px 12px', color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.3)' }}>
              <Trash2 size={13} /> Delete
            </GhostButton>
          )}
          <GhostButton onClick={() => setShowDetails(!showDetails)} style={{ gap: 5, fontSize: 12, padding: '5px 12px' }}>
            {showDetails ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </GhostButton>
        </div>
      </div>

      {showDetails && model.metrics?.length > 0 && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>
            Metric Weights
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 6 }}>
            {model.metrics.map(m => (
              <div key={m.id} style={{ background: 'var(--bg)', borderRadius: 'var(--radius-sm)', padding: '6px 10px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{m.feature_name}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--primary)' }}>{m.weight}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

const adminHero = { border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))', padding: 24, marginBottom: 24 }
const heroKicker = { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 }
const heroTitle = { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2rem, 5vw, 3.25rem)', lineHeight: 1, fontWeight: 900, maxWidth: 820 }
const heroSub = { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 760 }
const heroBadge = { display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-strong)', borderRadius: 999, padding: '6px 10px', color: 'var(--text-2)', fontSize: 12, fontWeight: 800 }
export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('models')
  const [models, setModels] = useState([])
  const [users, setUsers] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')
  const [msgType, setMsgType] = useState('info')
  const [showCreate, setShowCreate] = useState(false)
  const [newModel, setNewModel] = useState({
    model_name: '', model_type: 'rule_based', version: '1.0',
    description: '', feature_set_version: 'v3_12metrics',
    label_strategy: 'sector_median_12m', evaluation_horizon: '12m',
  })

  const notify = (text, type = 'info') => { setMsg(text); setMsgType(type) }

  const fetchModels = () => api.get('/admin/scoring-models').then(({ data }) => setModels(data)).catch(() => {})
  const fetchUsers = () => api.get('/admin/users').then(({ data }) => setUsers(data)).catch(() => {})
  const fetchAuditLogs = () => api.get('/admin/audit-logs?limit=50').then(({ data }) => setAuditLogs(data)).catch(() => {})

  useEffect(() => {
    fetchModels()
    if (activeTab === 'users') fetchUsers()
    if (activeTab === 'audit') fetchAuditLogs()
  }, [activeTab])

  const activateModel = async (id) => {
    try { await api.post(`/admin/scoring-models/${id}/activate`); notify('Model activated.', 'success'); fetchModels() }
    catch (e) { notify(e.response?.data?.detail || 'An error occurred.', 'error') }
  }
  const archiveModel = async (id) => {
    try { await api.post(`/admin/scoring-models/${id}/archive`); notify('Model archived.'); fetchModels() }
    catch (e) { notify(e.response?.data?.detail || 'An error occurred.', 'error') }
  }
  const deleteModel = async (id) => {
    if (!window.confirm('Are you sure you want to delete this model?')) return
    try { await api.delete(`/admin/scoring-models/${id}`); notify('Model deleted.'); fetchModels() }
    catch (e) { notify(e.response?.data?.detail || 'An error occurred.', 'error') }
  }
  const runValidation = async (modelId) => {
    setLoading(true)
    try {
      const { data } = await api.post('/validation/run', { scoring_model_id: modelId, train_ratio: 0.7 })
      notify(`Validation complete. F1: ${data.f1?.toFixed(3)} | AUC: ${data.roc_auc?.toFixed(3)}`, 'success')
      fetchModels()
    } catch (e) { notify(e.response?.data?.detail || 'Validation error.', 'error') }
    finally { setLoading(false) }
  }
  const createModel = async () => {
    try { await api.post('/admin/scoring-models', { ...newModel, metrics: [] }); notify('Model created.', 'success'); setShowCreate(false); fetchModels() }
    catch (e) { notify(e.response?.data?.detail || 'An error occurred.', 'error') }
  }
  const updateRole = async (userId, role) => {
    try { await api.patch(`/admin/users/${userId}/role?role=${role}`); notify('Role updated.'); fetchUsers() }
    catch (e) { notify(e.response?.data?.detail || 'An error occurred.', 'error') }
  }

  const msgBg = msgType === 'success' ? 'rgba(16,185,129,0.08)' : msgType === 'error' ? 'rgba(239,68,68,0.08)' : 'rgba(14,165,233,0.08)'
  const msgColor = msgType === 'success' ? 'var(--success)' : msgType === 'error' ? 'var(--danger)' : 'var(--primary)'

  const inputS = {
    width: '100%', boxSizing: 'border-box',
    background: 'var(--surface-1)', border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)', color: 'var(--text-1)',
    padding: '8px 12px', fontSize: 13, outline: 'none',
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <section style={adminHero}>
        <div style={heroKicker}><Sparkles size={15} /> Admin Console</div>
        <h1 style={heroTitle}>Model registry, users, and audit controls.</h1>
        <p style={heroSub}>Operational workspace for governance tasks. Keep active models, user roles, and validation events traceable.</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 }}>
          <span style={heroBadge}><Settings size={13} /> Registry control</span>
          <span style={heroBadge}><ShieldCheck size={13} /> Audit trail</span>
        </div>
      </section>

      {/* Toast */}
      {msg && (
        <div style={{
          background: msgBg, border: `1px solid ${msgColor}40`,
          borderRadius: 'var(--radius-md)', padding: '10px 14px',
          color: msgColor, fontSize: 13, marginBottom: 16,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span>{msg}</span>
          <button onClick={() => setMsg('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: msgColor, padding: 0, lineHeight: 1 }}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border)', marginBottom: 24 }}>
        {[['models', <Box size={14} />, 'Model Registry'], ['users', <Users size={14} />, 'Users'], ['audit', <ClipboardList size={14} />, 'Audit Log']].map(([key, icon, label]) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            style={{
              background: 'none', border: 'none', padding: '10px 18px', fontSize: 13, fontWeight: 500,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
              color: activeTab === key ? 'var(--primary)' : 'var(--text-3)',
              borderBottom: activeTab === key ? '2px solid var(--primary)' : '2px solid transparent',
              marginBottom: -1,
            }}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      {/* ── Model Registry ── */}
      {activeTab === 'models' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ fontSize: 13, color: 'var(--text-3)' }}>{models.length} model</div>
            <GhostButton onClick={() => setShowCreate(!showCreate)} style={{ gap: 6, fontSize: 13 }}>
              {showCreate ? <><X size={14} /> Cancel</> : <><Plus size={14} /> New Model</>}
            </GhostButton>
          </div>

          {showCreate && (
            <Card style={{ padding: '1.25rem', marginBottom: 16, borderColor: 'var(--primary-muted)' }}>
              <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-1)', marginBottom: 14 }}>Create New Model</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {[['model_name', 'Model Name'], ['version', 'Version'], ['feature_set_version', 'Feature Set'], ['label_strategy', 'Label Strategy'], ['evaluation_horizon', 'Horizon'], ['description', 'Description']].map(([field, label]) => (
                  <div key={field}>
                    <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 5 }}>{label}</label>
                    <input style={inputS} value={newModel[field] || ''} onChange={e => setNewModel(p => ({ ...p, [field]: e.target.value }))} />
                  </div>
                ))}
                <div>
                  <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 5 }}>Model Type</label>
                  <select style={inputS} value={newModel.model_type} onChange={e => setNewModel(p => ({ ...p, model_type: e.target.value }))}>
                    <option value="rule_based">Rule-Based</option>
                    <option value="logistic">Logistic Regression</option>
                    <option value="tree_based">Tree-Based</option>
                  </select>
                </div>
              </div>
              <button
                onClick={createModel}
                style={{ marginTop: 16, background: 'var(--primary)', border: 'none', borderRadius: 'var(--radius-md)', color: '#fff', padding: '9px 20px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
              >
                Create
              </button>
            </Card>
          )}

          {models.map(m => (
            <ModelCard key={m.id} model={m} onActivate={activateModel} onArchive={archiveModel} onDelete={deleteModel} onRunValidation={runValidation} />
          ))}
          {loading && <div style={{ color: 'var(--text-3)', textAlign: 'center', padding: '1.5rem' }}>Running validation...</div>}
          {models.length === 0 && !loading && (
            <EmptyState icon={<Box size={28} />} title="No models found" description="Create a new model." />
          )}
        </>
      )}

      {/* ── Users ── */}
      {activeTab === 'users' && (
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          {users.length === 0
            ? <div style={{ padding: '2rem' }}><EmptyState icon={<Users size={28} />} title="No users found" /></div>
            : users.map(u => (
              <div key={u.id} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '12px 16px', borderBottom: '1px solid var(--border)', gap: 12,
              }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-1)' }}>{u.email}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{new Date(u.created_at).toLocaleDateString('en-US')}</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <select
                    value={u.role}
                    onChange={e => updateRole(u.id, e.target.value)}
                    style={{ ...inputS, width: 130, padding: '6px 10px', fontSize: 12 }}
                  >
                    <option value="investor">investor</option>
                    <option value="analyst">analyst</option>
                    <option value="admin">admin</option>
                  </select>
                  <span style={{
                    ...statusChipStyle(u.is_active ? 'active' : 'archived'),
                    borderRadius: 'var(--radius-2xl)', padding: '2px 10px', fontSize: 11, fontWeight: 600
                  }}>
                    {u.is_active ? 'active' : 'inactive'}
                  </span>
                </div>
              </div>
            ))
          }
        </Card>
      )}

      {/* ── Audit Log ── */}
      {activeTab === 'audit' && (
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          {auditLogs.length === 0
            ? <div style={{ padding: '2rem' }}><EmptyState icon={<ClipboardList size={28} />} title="No audit logs yet" /></div>
            : auditLogs.map(log => (
              <div key={log.id} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: 16, flexShrink: 0, marginTop: 1 }}>
                  {ACTION_ICONS[log.action_type] || ACTION_ICONS.default}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, color: 'var(--text-1)', fontWeight: 600 }}>
                    {log.action_type.replace(/_/g, ' ')}
                  </div>
                  {log.description && <div style={{ fontSize: 12, color: 'var(--text-2)' }}>{log.description}</div>}
                  {log.entity_type && <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{log.entity_type} #{log.entity_id}</div>}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', whiteSpace: 'nowrap', flexShrink: 0 }}>
                  {new Date(log.created_at).toLocaleString('en-US')}
                </div>
              </div>
            ))
          }
        </Card>
      )}
    </div>
  )
}
