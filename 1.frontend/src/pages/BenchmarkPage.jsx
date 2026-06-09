import { useEffect, useState } from 'react'
import { BarChart3, Sparkles, Target } from 'lucide-react'
import { researchApi } from '../api/researchApi'
import { MetricCard, EvidencePanel, Bullets, SignalBadge, formatPercent, asText } from '../utils/safeRender'

export default function BenchmarkPage() {
  const [b, setB] = useState(null)
  useEffect(() => { researchApi.benchmark().then(r => setB(r.data)) }, [])

  const returns = b?.returns_by_year || {}
  const years = (b?.years_covered || Object.keys(returns).map(Number)).slice().sort((a, c) => a - c)
  const maxAbs = Math.max(1, ...years.map(y => Math.abs(Number(returns[y]) || 0)))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <section style={styles.hero}>
        <div>
          <div style={styles.kicker}><Sparkles size={15} /> Benchmark Layer</div>
          <h1 style={styles.title}>BIST100 turns raw returns into benchmark-aware targets.</h1>
          <p style={styles.subtitle}>
            Yearly index returns create excess-return and outperform-BIST100 labels for historical evaluation.
            Benchmark data is never fabricated; missing inputs disable benchmark-aware targets.
          </p>
          <div style={styles.badges}>
            <SignalBadge tone={b?.available ? 'good' : 'warn'}>{b?.available ? 'Benchmark available' : 'Benchmark missing'}</SignalBadge>
            <SignalBadge tone={b?.targets_enabled ? 'good' : 'warn'}>Targets {b?.targets_enabled ? 'enabled' : 'disabled'}</SignalBadge>
            <SignalBadge tone="bad">Research support only</SignalBadge>
          </div>
        </div>
        <div style={styles.formulaCard}>
          <Target size={22} color="var(--primary)" />
          <div style={styles.formulaTitle}>Target Derivation</div>
          <div style={styles.formulaLine}>Excess return = stock next-year return - BIST100 next-year return</div>
          <div style={styles.formulaLine}>Outperformed BIST100 = excess return greater than zero</div>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(165px,1fr))', gap: 12 }}>
        <MetricCard label="Status" value={b?.available ? 'Available' : 'Missing'} tone={b?.available ? 'good' : 'warn'} />
        <MetricCard label="Source" value={asText(b?.source)} mono={false} />
        <MetricCard label="Years covered" value={asText(years.length)} sub={years.join(', ')} />
        <MetricCard label="Excess / outperform" value={b?.targets_enabled ? 'Enabled' : 'Disabled'} tone={b?.targets_enabled ? 'good' : 'warn'} mono={false} />
      </div>

      {/* Yearly returns with proportional bars */}
      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 14 }}>
          <span style={styles.chartIcon}><BarChart3 size={17} /></span>
          <div>
            <div style={{ fontSize: 13.5, fontWeight: 800, color: 'var(--text-1)' }}>BIST100 yearly return</div>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>Proportional bars show annual benchmark movement</div>
          </div>
        </div>
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
            'BIST100 next-year return: the index return in the target year.',
            'Excess return vs BIST100: stock next-year return minus BIST100 next-year return.',
            'Outperformed BIST100: true when excess return is greater than zero.',
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

const styles = {
  hero: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))',
    gap: 18,
    alignItems: 'stretch',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    background: 'linear-gradient(135deg, rgba(85,194,195,0.13), rgba(244,176,74,0.08) 44%, var(--surface-2))',
    padding: 24,
  },
  kicker: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    color: 'var(--primary-hover)',
    background: 'var(--primary-subtle)',
    border: '1px solid rgba(244,176,74,0.25)',
    borderRadius: 999,
    padding: '5px 11px',
    fontSize: 12,
    fontWeight: 800,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
  },
  title: {
    margin: '14px 0 8px',
    color: 'var(--text-1)',
    fontSize: 'clamp(2rem, 5vw, 3.35rem)',
    lineHeight: 1,
    fontWeight: 900,
    maxWidth: 820,
  },
  subtitle: {
    color: 'var(--text-2)',
    fontSize: 14.5,
    lineHeight: 1.65,
    margin: 0,
    maxWidth: 740,
  },
  badges: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
  },
  formulaCard: {
    background: 'rgba(8,15,26,0.54)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: 18,
    display: 'flex',
    flexDirection: 'column',
    gap: 9,
  },
  formulaTitle: {
    color: 'var(--text-1)',
    fontSize: 18,
    fontWeight: 900,
  },
  formulaLine: {
    color: 'var(--text-2)',
    fontSize: 12.8,
    lineHeight: 1.5,
    background: 'var(--surface-1)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: '9px 10px',
  },
  chartIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    background: 'var(--primary-subtle)',
    color: 'var(--primary-hover)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
}
