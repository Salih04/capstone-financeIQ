import { useEffect, useMemo, useState } from 'react'
import { FlaskConical } from 'lucide-react'
import { Card, SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, WarningCallout, formatNumber, asText } from '../utils/safeRender'

export default function ExperimentsPage() {
  const [exp, setExp] = useState(null)
  const [target, setTarget] = useState('next_year_return_pct')

  useEffect(() => { researchApi.experiments().then(r => setExp(r.data)) }, [])

  const targets = exp?.available_targets || ['next_year_return_pct']
  const diag = exp?.diagnostics || {}
  const byTarget = exp?.leaderboard_by_target || []
  const primaryLb = exp?.leaderboard || []

  const rows = useMemo(() => {
    if (target === 'next_year_return_pct' && byTarget.length === 0) {
      return primaryLb.map(r => ({ ...r, target }))
    }
    return byTarget.filter(r => r.target === target)
  }, [byTarget, primaryLb, target])

  const cols = ['split', 'model', 'kind', 'mae', 'rmse', 'spearman', 'precision_at_5', 'directional_acc']

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader title="Experiments — walk-forward backtest" sub="Honest out-of-sample evaluation" icon={FlaskConical}
        actions={
          <select value={target} onChange={e => setTarget(e.target.value)} style={sel}>
            {targets.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        } />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px,1fr))', gap: 12 }}>
        <MetricCard label="Primary target" value="next_year_return_pct" />
        <MetricCard label="Mean Spearman" value={asText(diag.mean_spearman)} tone={diag.weak_backtest ? 'bad' : 'good'} />
        <MetricCard label="Weak backtest" value={asText(diag.weak_backtest)} tone={diag.weak_backtest ? 'bad' : 'good'} />
        <MetricCard label="ML beats baseline" value={asText(diag.ml_beats_baseline_consistently)} tone={diag.ml_beats_baseline_consistently ? 'good' : 'bad'} />
        <MetricCard label="Small sample" value={asText(diag.small_sample)} tone="warn" />
      </div>

      <WarningCallout title="Model quality verdict" tone="bad">
        {asText(exp?.verdict)} ~40 stocks/year — single-split spikes are noise, not skill. Trust baselines over ML.
      </WarningCallout>

      <Card>
        <SectionHeader title={`Leaderboard — ${target}`} sub="baseline vs ML across walk-forward splits" />
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--text-3)' }}>
                {cols.map(c => <th key={c} style={th}>{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={cols.length} style={{ padding: 12, color: 'var(--text-3)' }}>No rows.</td></tr>}
              {rows.map((r, i) => (
                <tr key={i} style={{ background: r.kind === 'baseline' ? 'var(--surface-2)' : 'transparent' }}>
                  {cols.map(c => (
                    <td key={c} style={td}>
                      {c === 'spearman' || c === 'directional_acc' ? formatNumber(r[c], 3)
                        : c === 'mae' || c === 'rmse' ? formatNumber(r[c], 1)
                        : asText(r[c])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card>
        <SectionHeader title="Metrics explained" />
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.7 }}>
          <li><b>Spearman</b>: rank correlation of predicted vs realized next-year return. Near 0 = no edge.</li>
          <li><b>precision@5</b>: of the top-5 predicted, how many were truly top-5. 0.2 ≈ random.</li>
          <li><b>directional_acc</b>: above/below median direction match. ~0.5 = coin flip.</li>
          <li><b>baseline</b> = equal-weight rank score; ML must beat it to matter (it does not here).</li>
        </ul>
      </Card>

      <Card>
        <SectionHeader title="Benchmark-aware targets" />
        <p style={{ fontSize: 13, color: 'var(--text-2)' }}>
          Targets <code>next_year_excess_return_vs_bist100</code> and <code>next_year_outperform_bist100</code> are
          evaluated when BIST100 is available. On current data they do <b>not</b> change the interpretation —
          the static feature set carries no reliable edge regardless of target.
        </p>
      </Card>
    </div>
  )
}

const sel = { background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '8px 12px', fontSize: 13 }
const th = { padding: '8px 10px', whiteSpace: 'nowrap', borderBottom: '1px solid var(--border)' }
const td = { padding: '7px 10px', whiteSpace: 'nowrap' }
