import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  Bot,
  Building2,
  Database,
  FlaskConical,
  LineChart,
  ShieldCheck,
  Sparkles,
  TrendingDown,
} from 'lucide-react'
import { researchApi } from '../api/researchApi'
import { MetricCard, RealityCheckCard, SignalBadge, asText, NOT_ADVICE } from '../utils/safeRender'

export default function DashboardPage() {
  const nav = useNavigate()
  const [summary, setSummary] = useState(null)
  const [bench, setBench] = useState(null)
  const [diag, setDiag] = useState(null)

  useEffect(() => {
    researchApi.summary().then((r) => setSummary(r.data))
    researchApi.benchmark().then((r) => setBench(r.data))
    researchApi.diagnostics().then((r) => setDiag(r.data))
  }, [])

  const ctx = summary?.context || {}
  const dgx = diag?.diagnostics || {}
  const benchOk = bench?.available || ctx.benchmark_available
  const valid = ctx.valid_for_modeling
  const weak = dgx.weak_backtest

  return (
    <div style={styles.page}>
      <section style={styles.hero}>
        <div style={styles.heroContent}>
          <div style={styles.kicker}>
            <Sparkles size={15} />
            FinanceIQ Research Terminal
          </div>
          <h1 style={styles.title}>Validated BIST research support, built for honest diagnostics.</h1>
          <p style={styles.subtitle}>
            Leakage-safe T to T+1 methodology across 40 selected BIST companies, validated project data,
            BIST100 benchmarking, and an AI assistant that explains findings without turning them into
            investment advice.
          </p>
          <div style={styles.heroActions}>
            <button type="button" onClick={() => nav('/research-agent')} style={styles.primaryBtn}>
              <Bot size={16} />
              Open Assistant
            </button>
            <button type="button" onClick={() => nav('/research')} style={styles.secondaryBtn}>
              <LineChart size={16} />
              Score Explorer
            </button>
          </div>
        </div>

        <div style={styles.verdictPanel}>
          <div style={styles.panelIcon}><TrendingDown size={20} /></div>
          <div style={styles.panelLabel}>Capstone Verdict</div>
          <div style={styles.panelTitle}>Pipeline complete; reliable predictive edge not demonstrated.</div>
          <p style={styles.panelText}>
            Weak or unstable signal is a valid research result. Data quality, leakage safety, and benchmark
            framing are strengths; predictive lift needs larger history or broader universe.
          </p>
          <SignalBadge tone="bad">Diagnostic, not investment advice</SignalBadge>
        </div>
      </section>

      <section style={styles.kpiGrid}>
        <MetricCard label="Dataset" value={valid ? 'Valid' : asText(valid)} tone={valid ? 'good' : 'warn'} sub="T to T+1 modeling set" mono={false} />
        <MetricCard label="Rows" value={asText(ctx.rows)} sub="40 companies x 6 years" />
        <MetricCard label="Target rows" value={asText(ctx.rows_with_target)} sub={`${asText(ctx.inference_only_rows)} inference-only`} />
        <MetricCard label="Validated features" value={asText(ctx.feature_count)} tone="good" sub="year-varying inputs" />
        <MetricCard label="Benchmark" value={benchOk ? 'Available' : 'Missing'} tone={benchOk ? 'good' : 'warn'} sub={asText(bench?.source || ctx.benchmark_source)} mono={false} />
        <MetricCard label="Model signal" value={weak ? 'Weak' : 'Stable'} tone={weak ? 'bad' : 'good'} sub={`Spearman ${asText(dgx.mean_spearman)}`} mono={false} />
      </section>

      <section style={styles.statusGrid}>
        <RealityCheckCard
          title="Research Reality Check"
          sub="Honest, academically defensible status"
          items={[
            { tone: 'good', text: 'T to T+1 target construction is leakage-safe and reproducible.' },
            { tone: 'good', text: `${asText(ctx.feature_count)} validated features support company-level diagnostics.` },
            { tone: 'good', text: 'BIST100 benchmark enables excess-return and outperform target analysis.' },
            { tone: 'warn', text: 'Current backtests show weak or unstable predictive relationship.' },
            { tone: 'info', text: 'A larger stock universe or longer history is the realistic path to stronger signal.' },
          ]}
        />

        <div style={styles.nextPanel}>
          <div style={styles.sectionEyebrow}>Next Actions</div>
          <ActionRow icon={Bot} title="Ask the AI Research Assistant" sub="Grounded answers from validated project data" onClick={() => nav('/research-agent')} />
          <ActionRow icon={Building2} title="Review Research Universe" sub="Ranked company cards and score context" onClick={() => nav('/research/companies')} />
          <ActionRow icon={FlaskConical} title="Inspect Experiments" sub="Backtests, baselines, and weak-signal interpretation" onClick={() => nav('/experiments')} />
          <ActionRow icon={Database} title="Audit Data Quality" sub="Corrected yearly financials and leakage controls" onClick={() => nav('/data-quality')} />
        </div>
      </section>

      <section>
        <div style={styles.sectionEyebrow}>Research Terminal</div>
        <div style={styles.cardGrid}>
          {[
            ['AI Research Assistant', Bot, '/research-agent', 'Plain-English research support'],
            ['Companies', Building2, '/research/companies', 'Ranked universe and score bars'],
            ['Experiments', FlaskConical, '/experiments', 'Walk-forward backtests'],
            ['Data Quality', Database, '/data-quality', 'Audit and integrity dashboard'],
            ['Benchmark', LineChart, '/benchmark', 'BIST100 yearly returns'],
          ].map(([label, Icon, to, sub]) => (
            <NavCard key={to} label={label} Icon={Icon} sub={sub} onClick={() => nav(to)} />
          ))}
        </div>
      </section>

      <div style={styles.disclaimer}>
        <ShieldCheck size={13} />
        {NOT_ADVICE}
      </div>
    </div>
  )
}

function ActionRow({ icon: Icon, title, sub, onClick }) {
  return (
    <button type="button" onClick={onClick} style={styles.actionRow}>
      <span style={styles.actionIcon}><Icon size={17} /></span>
      <span style={{ minWidth: 0 }}>
        <span style={styles.actionTitle}>{title}</span>
        <span style={styles.actionSub}>{sub}</span>
      </span>
      <ArrowRight size={16} style={{ color: 'var(--text-3)', marginLeft: 'auto', flexShrink: 0 }} />
    </button>
  )
}

function NavCard({ label, Icon, sub, onClick }) {
  const [hover, setHover] = useState(false)
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ ...styles.navCard, ...(hover ? styles.navCardHover : {}) }}
    >
      <span style={styles.navIcon}><Icon size={19} /></span>
      <span style={styles.navText}>
        <span style={styles.navTitle}>{label}</span>
        <span style={styles.navSub}>{sub}</span>
      </span>
    </button>
  )
}

const styles = {
  page: {
    maxWidth: 1240,
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: 20,
  },
  hero: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))',
    gap: 20,
    alignItems: 'stretch',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    background: 'linear-gradient(135deg, rgba(244,176,74,0.14), rgba(85,194,195,0.08) 44%, var(--surface-2))',
    padding: 24,
    overflow: 'hidden',
  },
  heroContent: {
    minWidth: 0,
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
    margin: '16px 0 10px',
    color: 'var(--text-1)',
    fontSize: 'clamp(2.15rem, 5vw, 4rem)',
    lineHeight: 1,
    fontWeight: 900,
    maxWidth: 860,
  },
  subtitle: {
    color: 'var(--text-2)',
    fontSize: 15,
    lineHeight: 1.65,
    margin: 0,
    maxWidth: 760,
  },
  heroActions: {
    display: 'flex',
    gap: 10,
    flexWrap: 'wrap',
    marginTop: 22,
  },
  primaryBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    background: 'var(--primary)',
    color: '#0b111a',
    border: 0,
    borderRadius: 'var(--radius-md)',
    padding: '10px 16px',
    fontSize: 13,
    fontWeight: 800,
    cursor: 'pointer',
  },
  secondaryBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(255,255,255,0.04)',
    color: 'var(--text-1)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: '10px 16px',
    fontSize: 13,
    fontWeight: 800,
    cursor: 'pointer',
  },
  verdictPanel: {
    background: 'rgba(8,15,26,0.54)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: 18,
    display: 'flex',
    flexDirection: 'column',
    gap: 9,
  },
  panelIcon: {
    width: 42,
    height: 42,
    borderRadius: 12,
    background: 'var(--warning-subtle)',
    color: 'var(--warning)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  panelLabel: {
    color: 'var(--warning-light)',
    fontSize: 11,
    fontWeight: 900,
    textTransform: 'uppercase',
    letterSpacing: 0.9,
  },
  panelTitle: {
    color: 'var(--text-1)',
    fontSize: 18,
    fontWeight: 900,
    lineHeight: 1.25,
  },
  panelText: {
    color: 'var(--text-2)',
    fontSize: 12.8,
    lineHeight: 1.6,
    margin: 0,
  },
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(165px,1fr))',
    gap: 12,
  },
  statusGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))',
    gap: 16,
  },
  nextPanel: {
    background: 'var(--surface-2)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    padding: 18,
  },
  sectionEyebrow: {
    color: 'var(--text-3)',
    fontSize: 11,
    fontWeight: 900,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
  },
  actionRow: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: 11,
    textAlign: 'left',
    background: 'transparent',
    color: 'inherit',
    border: 0,
    borderTop: '1px solid var(--border)',
    padding: '12px 0',
    cursor: 'pointer',
    font: 'inherit',
  },
  actionIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    background: 'var(--primary-subtle)',
    color: 'var(--primary-hover)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  actionTitle: {
    display: 'block',
    color: 'var(--text-1)',
    fontSize: 13.5,
    fontWeight: 800,
  },
  actionSub: {
    display: 'block',
    color: 'var(--text-3)',
    fontSize: 12,
    marginTop: 2,
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(210px,1fr))',
    gap: 12,
  },
  navCard: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    textAlign: 'left',
    background: 'var(--surface-2)',
    color: 'inherit',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    padding: 16,
    cursor: 'pointer',
    font: 'inherit',
    transition: 'border-color .15s, transform .12s, box-shadow .15s',
  },
  navCardHover: {
    borderColor: 'var(--border-bright)',
    transform: 'translateY(-2px)',
    boxShadow: 'var(--shadow-sm)',
  },
  navIcon: {
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
  navText: {
    minWidth: 0,
  },
  navTitle: {
    display: 'block',
    color: 'var(--text-1)',
    fontSize: 14,
    fontWeight: 900,
  },
  navSub: {
    display: 'block',
    color: 'var(--text-3)',
    fontSize: 11.5,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  disclaimer: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    alignSelf: 'center',
    color: 'var(--text-3)',
    fontSize: 11.5,
    fontWeight: 700,
  },
}
