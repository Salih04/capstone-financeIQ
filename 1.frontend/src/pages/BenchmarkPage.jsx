import { useEffect, useState } from 'react'
import { LineChart } from 'lucide-react'
import { SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, EvidencePanel, Bullets, formatPercent, asText } from '../utils/safeRender'

export default function BenchmarkPage() {
  const [b, setB] = useState(null)
  useEffect(() => { researchApi.benchmark().then(r => setB(r.data)) }, [])

  const returns = b?.returns_by_year || {}
  const years = (b?.years_covered || Object.keys(returns).map(Number)).slice().sort((a, c) => a - c)
  const maxAbs = Math.max(1, ...years.map(y => Math.abs(Number(returns[y]) || 0)))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <SectionHeader title="BIST100 Benchmark" sub="Yearly index returns used for excess / outperform targets" icon={LineChart} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(165px,1fr))', gap: 12 }}>
        <MetricCard label="Status" value={b?.available ? 'Available' : 'Missing'} tone={b?.available ? 'good' : 'warn'} />
        <MetricCard label="Source" value={asText(b?.source)} mono={false} />
        <MetricCard label="Years covered" value={asText(years.length)} sub={years.join(', ')} />
        <MetricCard label="Excess / outperform" value={b?.targets_enabled ? 'Enabled' : 'Disabled'} tone={b?.targets_enabled ? 'good' : 'warn'} mono={false} />
      </div>

      {/* Yearly returns with proportional bars */}
      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 14 }}>BIST100 yearly return</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
          {years.map(y => {
            const v = Number(returns[y])
            const pos = v >= 0
            const w = Math.max(2, (Math.abs(v) / maxAbs) * 100)
            const color = pos ? 'var(--success)' : 'var(--danger)'
            return (
              <div key={y} style={{ display: 'grid', gridTemplateColumns: '52px 1fr 72px', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-2)', fontVariantNumeric: 'tabular-nums' }}>{y}</span>
                <div style={{ height: 12, background: 'var(--surface-1)', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${w}%`, background: color, borderRadius: 999, transition: 'width .3s' }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 800, textAlign: 'right', color, fontVariantNumeric: 'tabular-nums' }}>
                  {formatPercent(v)}
                </span>
              </div>
            )
          })}
          {years.length === 0 && <div style={{ color: 'var(--text-3)', fontSize: 13 }}>No benchmark data.</div>}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px,1fr))', gap: 16 }}>
        <EvidencePanel title="What benchmark-adjusted targets mean" tone="info">
          <Bullets size={12.5} items={[
            'next_year_bist100_return_pct — the index return in the target year.',
            'next_year_excess_return_vs_bist100 — stock next-year return minus BIST100 next-year return.',
            'next_year_outperform_bist100 — true when excess return is greater than zero.',
          ]} />
        </EvidencePanel>
        <EvidencePanel title="Source & fallback" tone="neutral"
          footer="Yearly return = (last close ÷ first close − 1) × 100. Never fabricated.">
          <Bullets size={12.5} items={[
            'Primary: Yahoo Finance chart API for XU100.IS (no key / paid API).',
            'Fallback: manual daily CSV (data/trusted_raw/bist100_daily.csv, accepts Turkish number formats).',
            'Last resort: template — flagged as unavailable rather than faked.',
          ]} />
        </EvidencePanel>
      </div>

      {b?.explanation ? (
        <p style={{ fontSize: 12, color: 'var(--text-3)', margin: 0 }}>{asText(b.explanation)}</p>
      ) : null}
    </div>
  )
}
