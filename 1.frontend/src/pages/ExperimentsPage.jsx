import { useEffect, useMemo, useState } from 'react'
import { FlaskConical } from 'lucide-react'
import { SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import {
  MetricCard, WarningCallout, CompactTable, SignalBadge, Collapsible, Bullets,
  formatNumber, asText,
} from '../utils/safeRender'

const TARGET_LABELS = {
  next_year_return_pct: 'Raw return',
  next_year_excess_return_vs_bist100: 'Excess vs BIST100',
  next_year_outperform_bist100: 'Outperform BIST100',
}
const label = (t) => TARGET_LABELS[t] || t
const naNum = (v, d) => (v === null || v === undefined || Number.isNaN(Number(v))) ? 'N/A' : formatNumber(v, d)

// internal split/model IDs -> end-user friendly labels
const splitLabel = (s) => {
  const m = String(s || '').match(/(20\d{2})/)
  return m ? `${m[1]} evaluation` : asTextSafe(s)
}
const MODEL_LABELS = {
  baseline_equal_weight: 'Equal-weight baseline',
  baseline_rank_score: 'Simple ranking baseline',
  linear_regression: 'Linear regression',
  ridge: 'Ridge regression',
  lasso: 'Lasso regression',
  elasticnet: 'Elastic net',
  random_forest: 'Random forest',
}
const modelLabel = (m) => MODEL_LABELS[m] || String(m || '').replace(/_/g, ' ')
const asTextSafe = (v) => (v === null || v === undefined || v === '') ? '—' : String(v)

export default function ExperimentsPage() {
  const [exp, setExp] = useState(null)
  const [target, setTarget] = useState('next_year_return_pct')

  useEffect(() => { researchApi.experiments().then(r => setExp(r.data)) }, [])

  const targets = exp?.available_targets || ['next_year_return_pct']
  const diag = exp?.diagnostics || {}
  const byTarget = exp?.leaderboard_by_target || []
  const primaryLb = exp?.leaderboard || []
  const weak = diag.weak_backtest

  const rows = useMemo(() => {
    const base = (target === 'next_year_return_pct' && byTarget.length === 0)
      ? primaryLb.map(r => ({ ...r, target }))
      : byTarget.filter(r => r.target === target)
    return base.map(r => ({ ...r, __baseline: r.kind === 'baseline' }))
  }, [byTarget, primaryLb, target])

  const columns = [
    { key: 'split', label: 'Evaluated on' },
    { key: 'model', label: 'Model' },
    { key: 'kind', label: 'Type' },
    { key: 'spearman', label: 'Rank correlation', align: 'right' },
    { key: 'precision_at_5', label: 'Top-5 hit rate', align: 'right' },
    { key: 'directional_acc', label: 'Direction accuracy', align: 'right' },
  ]

  const renderCell = (c, r) => {
    if (c.key === 'split') return splitLabel(r.split)
    if (c.key === 'model') return modelLabel(r.model)
    if (c.key === 'kind') return <SignalBadge tone={r.__baseline ? 'info' : 'accent'}>{r.__baseline ? 'baseline' : 'model'}</SignalBadge>
    if (c.key === 'spearman' || c.key === 'directional_acc' || c.key === 'precision_at_5') return naNum(r[c.key], 3)
    return asText(r[c.key])
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <SectionHeader title="Experiments — walk-forward backtest" sub="Honest out-of-sample evaluation · benchmark-aware targets" icon={FlaskConical} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(165px,1fr))', gap: 12 }}>
        <MetricCard label="Target" value="Next-year return" mono={false} sub="evaluated out-of-sample" />
        <MetricCard label="Mean rank correlation" value={naNum(diag.mean_spearman, 3)} tone={weak ? 'bad' : 'good'} sub="≈0 = no edge" />
        <MetricCard label="Signal quality" value={weak ? 'Weak' : 'OK'} tone={weak ? 'bad' : 'good'} mono={false} />
        <MetricCard label="ML beats baseline" value={diag.ml_beats_baseline_consistently ? 'Yes' : 'No'} tone={diag.ml_beats_baseline_consistently ? 'good' : 'bad'} mono={false} />
        <MetricCard label="Sample" value={diag.small_sample ? 'Small' : 'OK'} tone="warn" mono={false} sub="~40 stocks/year" />
      </div>

      <WarningCallout title="No reliable predictive edge yet" tone="bad">
        {asText(exp?.verdict)} With ~40 stocks per year, single-split spikes are noise, not skill —
        trust the baselines over the ML model on the current feature set.
      </WarningCallout>

      {exp?.interpretation_business?.length ? (
        <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>What this means in plain terms</div>
          <Bullets size={12.5} items={exp.interpretation_business} />
        </div>
      ) : null}

      {/* Target tabs */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {targets.map(t => {
          const active = t === target
          return (
            <button key={t} onClick={() => setTarget(t)} title={t}
              style={{ background: active ? 'var(--primary-subtle)' : 'var(--surface-2)',
                color: active ? 'var(--primary-hover)' : 'var(--text-2)',
                border: `1px solid ${active ? 'var(--primary)' : 'var(--border-strong)'}`,
                borderRadius: 999, padding: '6px 14px', fontSize: 12.5, fontWeight: 700, cursor: 'pointer' }}>
              {label(t)}
            </button>
          )
        })}
      </div>

      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
        <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 4 }}>Leaderboard — {label(target)}</div>
        <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginBottom: 12 }}>Baseline rows shaded · ML must beat baseline to matter</div>
        <CompactTable columns={columns} rows={rows} highlight={r => r.__baseline} renderCell={renderCell} empty="No rows for this target." />
      </div>

      <Collapsible label="What these metrics mean">
        <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
          <Bullets size={12.5} items={[
            'Rank correlation — how well predicted ranking matches realized next-year return. Near 0 = no edge. N/A = constant predictions.',
            'Top-5 hit rate — of the top-5 predicted, how many were truly top-5. ≈0.2 is random.',
            'Direction accuracy — above/below-median direction match. ≈0.5 is a coin flip.',
            'Baseline — a simple equal-weight/ranking model; the ML models must beat it consistently to add value (they do not here).',
          ]} />
        </div>
      </Collapsible>

      <EvidenceNote />
    </div>
  )
}

function EvidenceNote() {
  return (
    <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>Benchmark-aware targets</div>
      <p style={{ fontSize: 12.5, color: 'var(--text-2)', margin: 0, lineHeight: 1.55 }}>
        Excess-return and outperform-BIST100 targets are evaluated when the benchmark is available. On the
        current data they do not change the conclusion — the static feature set carries no reliable edge
        regardless of target. A constant prediction yields an undefined Spearman, shown as N/A.
      </p>
    </div>
  )
}
