import { useEffect, useMemo, useState } from 'react'
import { Activity, BarChart3, FlaskConical, ShieldCheck, Sparkles, TrendingDown } from 'lucide-react'
import { researchApi } from '../api/researchApi'
import {
  MetricCard, WarningCallout, CompactTable, SignalBadge, Collapsible, Bullets,
  formatNumber, asText,
} from '../utils/safeRender'
import TerminalFx from '../components/TerminalFx'

const TARGET_LABELS = {
  next_year_return_pct: 'Next-year return',
  next_year_excess_return_vs_bist100: 'Excess vs BIST100',
  next_year_outperform_bist100: 'Outperform BIST100',
}
const label = (t) => TARGET_LABELS[t] || t
const naNum = (v, d) => (v === null || v === undefined || Number.isNaN(Number(v))) ? 'N/A' : formatNumber(v, d)

// internal split/model IDs -> end-user friendly labels
const splitLabel = (s) => {
  const m = String(s || '').match(/(20\d{2})/)
  return m ? `${m[1]} Backtest` : asTextSafe(s)
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

  const bestRow = rows
    .filter(r => r.kind !== 'baseline')
    .slice()
    .sort((a, b) => (Number(b.spearman) || -1e9) - (Number(a.spearman) || -1e9))[0]

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
    <div className="tfx tfx-enter" style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <TerminalFx />
      <section style={styles.hero}>
        <div>
          <div className="tfx-kicker" style={styles.kicker}><Sparkles size={13} /> WALK-FORWARD BACKTESTS</div>
          <h1 style={styles.title}>Experiments show weak signal, not a broken system.</h1>
          <p style={styles.subtitle}>
            Each split evaluates whether year-T features rank next-year outcomes better than simple baselines.
            Current evidence is honest: small sample, unstable relationships, no reliable predictive edge.
          </p>
          <div style={styles.heroBadges}>
            <SignalBadge tone="good"><ShieldCheck size={12} /> Leakage-safe targets</SignalBadge>
            <SignalBadge tone="info">{label(target)}</SignalBadge>
            <SignalBadge tone="bad">Research support only</SignalBadge>
          </div>
        </div>
        <div style={styles.verdictCard}>
          <TrendingDown size={22} color="var(--warning)" />
          <div style={styles.verdictLabel}>Experiment Verdict</div>
          <div style={styles.verdictTitle}>{diag.ml_beats_baseline_consistently ? 'ML adds signal' : 'ML does not beat baseline consistently'}</div>
          <p style={styles.verdictText}>{asText(exp?.verdict)}</p>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(165px,1fr))', gap: 12 }}>
        <MetricCard label="Selected target" value={label(target)} mono={false} sub="evaluated out-of-sample" />
        <MetricCard label="Mean rank correlation" value={naNum(diag.mean_spearman, 3)} tone={weak ? 'bad' : 'good'} sub="≈0 = no edge" />
        <MetricCard label="Signal quality" value={weak ? 'Weak' : 'OK'} tone={weak ? 'bad' : 'good'} mono={false} />
        <MetricCard label="ML beats baseline" value={diag.ml_beats_baseline_consistently ? 'Yes' : 'No'} tone={diag.ml_beats_baseline_consistently ? 'good' : 'bad'} mono={false} />
        <MetricCard label="Sample" value={diag.small_sample ? 'Small' : 'OK'} tone="warn" mono={false} sub="about 40 stocks/year" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px,1fr))', gap: 14 }}>
        <Insight icon={Activity} title="Target in focus" value={label(target)} sub="User-selectable evaluation outcome" />
        <Insight icon={BarChart3} title="Best ML row" value={bestRow ? modelLabel(bestRow.model) : 'No model row'} sub={bestRow ? `${splitLabel(bestRow.split)} · Spearman ${naNum(bestRow.spearman, 3)}` : 'Leaderboard unavailable'} />
        <Insight icon={FlaskConical} title="Baseline meaning" value="Simple comparator" sub="ML must beat simple ranking consistently to matter" />
      </div>

      <WarningCallout title="No reliable predictive edge yet" tone="bad">
        {asText(exp?.verdict)} With about 40 stocks per year, single-split spikes are noise, not skill.
        Baselines remain the correct benchmark for judging model value.
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
            <button key={t} onClick={() => setTarget(t)} title={t} className="tfx-tab"
              aria-pressed={active}
              style={{ background: active ? 'var(--primary-subtle)' : 'var(--surface-2)',
                color: active ? 'var(--primary-hover)' : 'var(--text-2)',
                border: `1px solid ${active ? 'var(--primary)' : 'var(--border-strong)'}`,
                borderRadius: 2, padding: '6px 14px', fontFamily: 'var(--font-mono)', fontSize: 11.5,
                fontWeight: 600, letterSpacing: '0.06em', cursor: 'pointer' }}>
              {label(t)}
            </button>
          )
        })}
      </div>

      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
        <div style={{ fontSize: 13.5, fontWeight: 800, marginBottom: 4 }}>Detailed leaderboard - {label(target)}</div>
        <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginBottom: 12 }}>Baseline rows shaded. Treat detailed rows as diagnostics, not ranking advice.</div>
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

function Insight({ icon: Icon, title, value, sub }) {
  return (
    <div style={styles.insight}>
      <span style={styles.insightIcon}><Icon size={18} /></span>
      <div>
        <div style={styles.insightTitle}>{title}</div>
        <div style={styles.insightValue}>{value}</div>
        <div style={styles.insightSub}>{sub}</div>
      </div>
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

const styles = {
  hero: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))',
    gap: 18,
    alignItems: 'stretch',
    border: '1px solid var(--border-strong)',
    borderLeft: '3px solid var(--secondary)',
    borderRadius: 'var(--radius-lg)',
    background: 'linear-gradient(135deg, rgba(200,163,90,0.12), rgba(77,165,131,0.07) 44%, var(--surface-2))',
    padding: 24,
  },
  kicker: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    color: 'var(--text-3)',
    background: 'rgba(10,14,13,0.5)',
    border: '1px solid var(--border-strong)',
    borderRadius: 2,
    padding: '5px 11px',
    fontSize: 10.5,
  },
  title: {
    margin: '14px 0 8px',
    color: 'var(--text-1)',
    fontSize: 'clamp(1.9rem, 4.4vw, 3rem)',
    lineHeight: 1.05,
    letterSpacing: '-0.015em',
    fontWeight: 650,
    maxWidth: 820,
  },
  subtitle: {
    color: 'var(--text-2)',
    fontSize: 14.5,
    lineHeight: 1.65,
    margin: 0,
    maxWidth: 740,
  },
  heroBadges: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
  },
  verdictCard: {
    background: 'rgba(10,14,13,0.6)',
    border: '1px solid var(--border-strong)',
    borderLeft: '3px solid var(--primary)',
    borderRadius: 'var(--radius-md)',
    padding: 18,
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  verdictLabel: {
    color: 'var(--warning-light)',
    fontFamily: 'var(--font-mono)',
    fontSize: 9.5,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.24em',
  },
  verdictTitle: {
    color: 'var(--text-1)',
    fontSize: 18,
    lineHeight: 1.25,
    fontWeight: 900,
  },
  verdictText: {
    color: 'var(--text-2)',
    fontSize: 12.5,
    lineHeight: 1.55,
    margin: 0,
  },
  insight: {
    display: 'flex',
    gap: 12,
    background: 'var(--surface-2)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    padding: 16,
  },
  insightIcon: {
    width: 38,
    height: 38,
    borderRadius: 10,
    background: 'var(--primary-subtle)',
    color: 'var(--primary-hover)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  insightTitle: {
    color: 'var(--text-3)',
    fontSize: 11,
    fontWeight: 900,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
  },
  insightValue: {
    color: 'var(--text-1)',
    fontSize: 16,
    fontWeight: 900,
    marginTop: 3,
  },
  insightSub: {
    color: 'var(--text-3)',
    fontSize: 12,
    lineHeight: 1.4,
    marginTop: 2,
  },
}
