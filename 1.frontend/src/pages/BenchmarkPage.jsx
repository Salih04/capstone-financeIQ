import { useEffect, useState } from 'react'
import { LineChart } from 'lucide-react'
import { Card, SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, RenderList, formatPercent, asText } from '../utils/safeRender'

export default function BenchmarkPage() {
  const [b, setB] = useState(null)
  useEffect(() => { researchApi.benchmark().then(r => setB(r.data)) }, [])

  const returns = b?.returns_by_year || {}
  const years = b?.years_covered || Object.keys(returns).map(Number)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader title="BIST100 Benchmark" sub="Yearly index returns used for excess/outperform targets" icon={LineChart} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px,1fr))', gap: 12 }}>
        <MetricCard label="Status" value={b?.available ? 'Available' : 'Missing'} tone={b?.available ? 'good' : 'warn'} />
        <MetricCard label="Source" value={asText(b?.source)} />
        <MetricCard label="Years covered" value={asText(years.length)} sub={years.join(', ')} />
        <MetricCard label="Excess/outperform targets" value={b?.targets_enabled ? 'enabled' : 'disabled'} tone={b?.targets_enabled ? 'good' : 'warn'} />
      </div>

      <Card>
        <SectionHeader title="BIST100 yearly return %" />
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead><tr style={{ color: 'var(--text-3)', textAlign: 'left' }}><th style={th}>Year</th><th style={th}>Return %</th><th style={th}>Bar</th></tr></thead>
            <tbody>
              {years.sort((a, b2) => a - b2).map(y => {
                const v = Number(returns[y])
                const w = Math.min(100, Math.abs(v) / 2)
                return (
                  <tr key={y}>
                    <td style={td}>{asText(y)}</td>
                    <td style={{ ...td, fontWeight: 700, color: v >= 0 ? 'var(--success,#16a34a)' : 'var(--danger,#dc2626)' }}>{formatPercent(v)}</td>
                    <td style={td}><div style={{ height: 8, width: `${w}%`, minWidth: 4, background: 'var(--accent,#6366f1)', borderRadius: 4 }} /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <Card>
        <SectionHeader title="How benchmark targets are created" />
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>
          <li><code>next_year_bist100_return_pct</code> — the index return in the target year.</li>
          <li><code>next_year_excess_return_vs_bist100</code> = stock next-year return − BIST100 next-year return.</li>
          <li><code>next_year_outperform_bist100</code> = excess &gt; 0.</li>
        </ul>
        <p style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 8 }}>{asText(b?.explanation)}</p>
        <div style={{ marginTop: 8 }}><RenderList items={b?.derived_targets} /></div>
      </Card>

      <Card>
        <SectionHeader title="Source & fallback" />
        <p style={{ fontSize: 13, color: 'var(--text-2)' }}>
          Collected by <code>make benchmark</code>: Yahoo Finance XU100.IS (no key/paid API) → manual daily CSV
          fallback (<code>data/trusted_raw/bist100_daily.csv</code>, accepts Turkish number formats) → template.
          Yearly return = (last close ÷ first close − 1) × 100. Never fabricated.
        </p>
      </Card>
    </div>
  )
}

const th = { padding: '8px 10px', borderBottom: '1px solid var(--border)' }
const td = { padding: '7px 10px' }
