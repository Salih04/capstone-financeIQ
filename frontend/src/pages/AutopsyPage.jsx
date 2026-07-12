import { useMemo, useState } from 'react'
import { useCachedResource, CACHE_TTL } from '../api/useCachedResource'
import { apiErrorText } from '../api/errorText'
import CacheTag from '../components/CacheTag'

const SOURCE = {
  instability: 'experiments/results/feature_stability_by_split.csv',
  stabilitySummary: 'experiments/results/feature_stability_summary.csv',
  overfit: 'experiments/leaderboard.csv',
  sparsity: 'experiments/results/coverage_impact.csv',
  significance: 'experiments/results/significance_report.json',
  power: 'experiments/results/significance_report.json · METHODOLOGY.md',
  regime: 'METHODOLOGY.md · experiments/results/significance_report.json',
  friction: 'experiments/results/friction_report.json · friction_plot.csv',
}

const FRICTION_STAMP = 'Hypothetical illustration — not a backtest of a viable strategy; underlying signal IC ≈ 0 and no model survives significance correction.'

const MODEL_LABELS = {
  baseline_equal_weight: 'Equal-weight baseline',
  random_forest: 'Random forest',
  gradient_boosting: 'Gradient boosting',
}

const FEATURE_LABELS = {
  benchmark_same_year_return_pct: 'Benchmark same-year return',
  price_data_available: 'Price data available',
  current_assets: 'Current assets',
  ebitda: 'EBITDA',
  gross_profit: 'Gross profit',
  revenue: 'Revenue',
  total_assets: 'Total assets',
  equity: 'Equity',
}

const signed = (value, digits = 3) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'N/A'
  return `${number >= 0 ? '+' : '−'}${Math.abs(number).toFixed(digits)}`
}

const fixed = (value, digits = 3) => {
  const number = Number(value)
  return Number.isFinite(number) ? number.toFixed(digits) : 'N/A'
}

const percent = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? `${number.toFixed(1)}%` : 'N/A'
}

function sourceRows(report, key) {
  return report?.evidence?.[key]?.rows || []
}

function buildInstability(report) {
  const rows = sourceRows(report, 'feature_stability_by_split')
  const summary = sourceRows(report, 'feature_stability_summary')
  const byFeature = new Map()
  rows.forEach((row) => {
    if (!byFeature.has(row.feature)) byFeature.set(row.feature, [])
    byFeature.get(row.feature).push(row)
  })

  return summary
    .filter((item) => {
      const values = (byFeature.get(item.feature) || [])
        .map((row) => Number(row.spearman_to_target))
        .filter(Number.isFinite)
      return values.some((value) => value < 0) && values.some((value) => value > 0)
    })
    .slice(0, 8)
    .map((item) => ({
      ...item,
      splits: (byFeature.get(item.feature) || []).sort((a, b) => String(a.split).localeCompare(String(b.split))),
    }))
}

function SourceLine({ children, limitation }) {
  return (
    <div className="ap-source">
      <span>SOURCE · {children}</span>
      <span>LIMITATION · {limitation}</span>
    </div>
  )
}

function EmptyPlot({ reason }) {
  return (
    <div className="ap-empty" role="status">
      <strong>DEMO FALLBACK · EVIDENCE UNAVAILABLE</strong>
      <span>{reason || 'The artifact API returned no rows; no values are substituted.'}</span>
    </div>
  )
}

function Exhibit({ number, label, title, children, finding, source, limitation, wide = false }) {
  return (
    <section className={`ap-exhibit ${wide ? 'is-wide' : ''}`} aria-labelledby={`ap-exhibit-${number}`}>
      <header className="ap-exhibit-head">
        <span className="ap-number">0{number}</span>
        <div>
          <div className="ap-label">{label}</div>
          <h2 id={`ap-exhibit-${number}`}>{title}</h2>
        </div>
      </header>
      <div className="ap-chart">{children}</div>
      <p className="ap-finding"><strong>FINDING · </strong>{finding}</p>
      <SourceLine limitation={limitation}>{source}</SourceLine>
    </section>
  )
}

function InstabilityChart({ report, reason }) {
  const features = useMemo(() => buildInstability(report), [report])
  if (!features.length) return <EmptyPlot reason={reason} />

  return (
    <div className="ap-instability" role="img" aria-label="Feature to target Spearman relationships that change sign across test splits">
      <div className="ap-instability-head"><span>FEATURE</span><span>2023</span><span>2024</span><span>2025</span></div>
      {features.map((feature) => (
        <div className="ap-instability-row" key={feature.feature}>
          <span title={feature.feature}>{FEATURE_LABELS[feature.feature] || feature.feature.replace(/_/g, ' ')}</span>
          {feature.splits.map((row) => (
            <span className={Number(row.spearman_to_target) >= 0 ? 'is-positive' : 'is-negative'} key={row.split}>
              {signed(row.spearman_to_target)}
            </span>
          ))}
        </div>
      ))}
    </div>
  )
}

function IcBar({ value }) {
  const number = Number(value)
  const width = Math.min(Math.abs(number) / 0.25, 1) * 50
  const left = number < 0 ? 50 - width : 50
  return (
    <div className="ap-ic-track">
      <span className="ap-zero" />
      <span className={number < 0 ? 'ap-ic-bar is-negative' : 'ap-ic-bar is-positive'} style={{ left: `${left}%`, width: `${width}%` }} />
    </div>
  )
}

function OverfitChart({ report, reason }) {
  const rows = sourceRows(report, 'leaderboard').filter((row) => MODEL_LABELS[row.model])
  if (!rows.length) return <EmptyPlot reason={reason} />

  return (
    <div className="ap-overfit" role="img" aria-label="Equal-weight baseline and tree model Spearman IC by split">
      {rows.map((row) => (
        <div className="ap-overfit-row" key={`${row.split}-${row.model}`}>
          <span>{String(row.split).replace('test_', '')} · {MODEL_LABELS[row.model]}</span>
          <IcBar value={row.spearman} />
          <strong>{signed(row.spearman)}</strong>
        </div>
      ))}
      <div className="ap-axis"><span>−0.25</span><span>IC 0</span><span>+0.25</span></div>
    </div>
  )
}

function SparsityChart({ report, reason }) {
  const rows = sourceRows(report, 'coverage_impact')
  if (!rows.length) return <EmptyPlot reason={reason} />
  const maxCount = Math.max(...rows.map((row) => Number(row.count)), 1)

  return (
    <div className="ap-sparsity" role="img" aria-label="Evaluated rows and descriptive nominal TRY outcomes by feature coverage bucket">
      {rows.map((row) => (
        <div className="ap-sparsity-row" key={row.coverage_bucket}>
          <span>{String(row.coverage_bucket).toUpperCase()}</span>
          <div className="ap-count-track"><span style={{ width: `${(Number(row.count) / maxCount) * 100}%` }} /></div>
          <strong>n={row.count}</strong>
          <small>mean {percent(row.mean_next_year_return_pct)} · median {percent(row.median_next_year_return_pct)}</small>
        </div>
      ))}
    </div>
  )
}

function SignificanceChart({ report, reason }) {
  const headline = report?.significance?.headline
  if (!headline) return <EmptyPlot reason={reason} />
  const values = [
    ['RAW TWO-SIDED P', headline.permutation_p_value_two_sided],
    ['BONFERRONI-ADJUSTED P', headline.bonferroni_adjusted_p_value],
  ]

  return (
    <div className="ap-significance" role="img" aria-label="Random forest raw and Bonferroni-adjusted p-values shown together">
      <div className="ap-sig-ic">
        <span>RANDOM FOREST · POOLED IC</span>
        <strong>{signed(headline.observed_ic)}</strong>
      </div>
      {values.map(([label, value]) => (
        <div className="ap-p-row" key={label}>
          <span>{label}</span>
          <div className="ap-p-track"><span style={{ width: `${Math.max(Number(value) * 100, 1.6)}%` }} /></div>
          <strong>{fixed(value, 4)}</strong>
        </div>
      ))}
      <div className="ap-alpha">family-wise α=0.05 · six ML models</div>
    </div>
  )
}

function PowerChart({ report, reason }) {
  const designs = report?.significance?.power_analysis?.designs || []
  const selected = [
    designs.find((item) => item.design_id === 'current_three_year_pooled'),
    designs.find((item) => item.design_id === 'current_one_split'),
  ].filter(Boolean)
  if (selected.length !== 2) return <EmptyPlot reason={reason} />
  const labels = ['THREE-YEAR DESIGN', 'ONE TEST YEAR']
  const max = 0.35

  return (
    <div className="ap-power" role="img" aria-label="Minimum detectable absolute IC for the current three-year and single-year designs">
      {selected.map((design, index) => (
        <div className="ap-power-row" key={design.design_id}>
          <span>{labels[index]}</span>
          <div className="ap-power-track">
            <span style={{ width: `${Math.min(Number(design.analytic_minimum_detectable_abs_ic) / max, 1) * 100}%` }} />
          </div>
          <strong>|IC| {fixed(design.analytic_minimum_detectable_abs_ic)}</strong>
          <small>n={design.n_per_split}/split · {design.split_count} split{design.split_count === 1 ? '' : 's'} · 80% power</small>
        </div>
      ))}
    </div>
  )
}

function RegimeStatement() {
  return (
    <div className="ap-regime" role="note">
      <strong>ONE OBSERVED MACRO WINDOW</strong>
      <p>2020–2025 · Regime robustness is untestable from a single extraordinary Turkish macro regime.</p>
      <small>Statement only · no regime-conditional chart is supported by the evidence.</small>
    </div>
  )
}

function FrictionChart({ friction, reason }) {
  const models = friction?.design?.models || []
  const scenarios = friction?.cost_scenarios || []
  const [selectedModel, setSelectedModel] = useState('random_forest')
  const [selectedScenario, setSelectedScenario] = useState('illustrative_100bps_assumption')
  if (!friction?.plot_rows?.length || !models.length || !scenarios.length) return <EmptyPlot reason={reason} />

  const model = models.includes(selectedModel) ? selectedModel : models[0]
  const scenario = scenarios.find((item) => item.scenario_id === selectedScenario) || scenarios[0]
  const rows = friction.plot_rows
    .filter((row) => row.model === model && row.scenario_id === scenario.scenario_id)
    .sort((a, b) => Number(a.year) - Number(b.year))
  if (!rows.length) return <EmptyPlot reason="The friction artifact has no rows for this model and scenario." />

  const finiteValues = rows.flatMap((row) => [row.gross_basket_mean_return_pct, row.net_basket_mean_return_pct])
    .map(Number)
    .filter(Number.isFinite)
  const maxAbs = Math.max(...finiteValues.map(Math.abs), 1)
  const zeroY = 176
  const barScale = 106 / maxAbs
  const geometry = (value) => {
    if (value == null) return null
    const numeric = Number(value)
    if (!Number.isFinite(numeric)) return null
    const height = Math.max(Math.abs(numeric) * barScale, 1)
    return { height, y: numeric >= 0 ? zeroY - height : zeroY }
  }
  const valueLabelY = (value, bar) => Number(value) >= 0
    ? Math.max(bar.y - 7, 62)
    : Math.min(bar.y + bar.height + 13, 248)
  const stamp = friction.chart_stamp === FRICTION_STAMP ? friction.chart_stamp : FRICTION_STAMP

  return (
    <div className="ap-friction-viz">
      <div className="ap-friction-controls">
        <label>
          MODEL
          <select value={model} onChange={(event) => setSelectedModel(event.target.value)}>
            {models.map((item) => <option value={item} key={item}>{item.replace(/_/g, ' ')}</option>)}
          </select>
        </label>
        <div className="ap-cost-controls" aria-label="Assumed cost scenarios">
          {scenarios.map((item) => (
            <button
              className={item.scenario_id === scenario.scenario_id ? 'is-active' : ''}
              type="button"
              onClick={() => setSelectedScenario(item.scenario_id)}
              key={item.scenario_id}
            >
              {Number(item.cost_bps).toLocaleString()} bps
            </button>
          ))}
        </div>
      </div>

      <svg className="ap-friction-svg" viewBox="0 0 920 300" role="img" aria-label={`Gross and assumed-cost net nominal TRY basket mean returns for ${model}`}>
        <rect className="ap-friction-bg" x="0" y="0" width="920" height="300" />
        <foreignObject x="18" y="12" width="884" height="42">
          <div className="ap-friction-stamp">{stamp}</div>
        </foreignObject>
        <line className="ap-friction-zero" x1="54" x2="884" y1={zeroY} y2={zeroY} />
        <text className="ap-friction-axis-label" x="12" y={zeroY + 3}>0%</text>
        {rows.map((row, index) => {
          const gross = geometry(row.gross_basket_mean_return_pct)
          const net = geometry(row.net_basket_mean_return_pct)
          const groupX = 170 + index * 260
          return (
            <g key={`${row.year}-${row.scenario_id}`}>
              {gross && <rect className="ap-friction-bar is-gross" x={groupX - 48} y={gross.y} width="54" height={gross.height} />}
              {net && <rect className="ap-friction-bar is-net" x={groupX + 18} y={net.y} width="54" height={net.height} />}
              <text className="ap-friction-value" x={groupX - 21} y={gross ? valueLabelY(row.gross_basket_mean_return_pct, gross) : 70} textAnchor="middle">
                {percent(row.gross_basket_mean_return_pct)}
              </text>
              <text className="ap-friction-value" x={groupX + 45} y={net ? valueLabelY(row.net_basket_mean_return_pct, net) : zeroY - 8} textAnchor="middle">
                {net ? percent(row.net_basket_mean_return_pct) : 'N/A'}
              </text>
              <text className="ap-friction-year" x={groupX + 12} y="260" textAnchor="middle">{row.year}</text>
              <text className="ap-friction-turnover" x={groupX + 12} y="278" textAnchor="middle">
                turnover {row.turnover_from_prior_year == null ? 'N/A' : fixed(row.turnover_from_prior_year, 2)}
              </text>
            </g>
          )
        })}
        <g className="ap-friction-legend">
          <rect className="ap-friction-bar is-gross" x="690" y="72" width="14" height="8" />
          <text x="710" y="80">GROSS</text>
          <rect className="ap-friction-bar is-net" x="780" y="72" width="14" height="8" />
          <text x="800" y="80">NET</text>
        </g>
      </svg>
      <div className="ap-friction-meta">
        <span>{scenario.role} · {Number(scenario.cost_bps).toLocaleString()} bps</span>
        <span>top-{friction.design.top_k} · equal weight · within-model ranks only</span>
      </div>
    </div>
  )
}

export default function AutopsyPage() {
  const { data: report, error, fromCache, refreshing, savedAt, refresh } =
    useCachedResource('/research/significance/autopsy', { ttlMs: CACHE_TTL.LONG })
  const hasEvidence = Boolean(report?.evidence && report?.significance)
  const hasFriction = Boolean(report?.friction?.plot_rows?.length)
  const reason = apiErrorText(error) || 'autopsy artifact API returned no evidence'

  return (
    <div className="ap">
      <style>{CSS}</style>
      <div className="ap-grid" aria-hidden="true" />

      <header className="ap-hero">
        <div>
          <div className="ap-kicker">FINANCEIQ · NEGATIVE ALPHA AUTOPSY</div>
          <h1>Anatomy of a signal <em>not found.</em></h1>
          <p>
            Six evidence exhibits examine instability, small-sample overfit, sparse coverage, multiplicity,
            design power, and regime limits. They explain the observed negative result without converting it
            into a positive claim.
          </p>
        </div>
        <div className={`ap-mode ${hasEvidence ? 'is-live' : 'is-fallback'}`}>
          <span>{hasEvidence ? 'LIVE ARTIFACT MODE' : 'DEMO FALLBACK · NO VALUES'}</span>
          <strong>{hasEvidence ? `4 CSV exhibits + significance report${hasFriction ? ' + friction sensitivity' : ''} loaded` : reason}</strong>
          <CacheTag fromCache={fromCache} refreshing={refreshing} savedAt={savedAt} onRefresh={refresh} />
        </div>
      </header>

      <div className="ap-caveat">
        This page documents evidence consistent with why no reliable signal was found: unstable feature relationships, overfitting under small n, sparse coverage, low statistical power, and a single macro regime. It explains the negative result; it does not promise a positive one under other conditions.
        <strong> Research support only · Not investment advice.</strong>
      </div>

      <main className="ap-exhibits">
        <Exhibit
          number={1}
          label="INSTABILITY"
          title="Feature relationships change sign."
          finding="The largest sign-changing feature–target rank relationships do not retain one direction across the three splits. This is consistent with unstable sample relationships; it does not prove instability caused the full negative result."
          source={`${SOURCE.instability} · ${SOURCE.stabilitySummary}`}
          limitation="descriptive training-split correlations, not model coefficients or causal effects"
          wide
        >
          <InstabilityChart report={report} reason={reason} />
        </Exhibit>

        <Exhibit
          number={2}
          label="OVERFIT"
          title="Tree IC stays below zero."
          finding="Random forest and gradient boosting have negative IC in all three test splits while the equal-weight baseline is positive in each. This is consistent with overfit under small n; it does not prove tree complexity alone caused the result."
          source={SOURCE.overfit}
          limitation="81-ticker training universe, n=80/split; three retrospectively fixed test years"
        >
          <OverfitChart report={report} reason={reason} />
        </Exhibit>

        <Exhibit
          number={3}
          label="SPARSITY"
          title="Coverage groups are uneven."
          finding="The low-, medium-, and high-coverage groups contain 33, 102, and 186 evaluated rows, with non-monotonic descriptive outcomes. This is consistent with coverage affecting sample composition; it does not prove missingness caused weak IC."
          source={SOURCE.sparsity}
          limitation="coverage buckets are artifact-defined; observed outcomes are nominal TRY and descriptive only"
        >
          <SparsityChart report={report} reason={reason} />
        </Exhibit>

        <Exhibit
          number={4}
          label="SIGNIFICANCE"
          title="The smallest raw p-value points downward."
          finding="The smallest raw p-value in the model family belongs to random forest at pooled IC −0.153 — the most “significant” model is significantly bad before correction, and nothing survives after it. Raw p=0.0183 and adjusted p=0.1098 stay paired. This is consistent with a multiple-comparisons trap; it does not prove a causal explanation."
          source={SOURCE.significance}
          limitation="Bonferroni family of six ML models; raw and adjusted p-values must be read together"
        >
          <SignificanceChart report={report} reason={reason} />
        </Exhibit>

        <Exhibit
          number={5}
          label="POWER"
          title="Small effects were below this design's reach."
          finding="The current design's minimum detectable |IC| is 0.182 across three years and 0.309 for one 80-row year. This is consistent with low power for smaller effects; it does not prove a smaller true effect exists. The detectable threshold is not a hard significance cutoff and does not estimate the true IC."
          source={SOURCE.power}
          limitation="one prespecified α=0.05 test; not Bonferroni-adjusted family-wise power"
        >
          <PowerChart report={report} reason={reason} />
        </Exhibit>

        <Exhibit
          number={6}
          label="REGIME"
          title="One macro regime cannot test robustness."
          finding="Nominal TRY returns span one extraordinary 2020–2025 Turkish macro regime. This is consistent with limited external validity; it does not prove the regime caused weak IC or that a different regime would produce a positive result."
          source={SOURCE.regime}
          limitation="no regime-conditional statistics are possible; reproduction is numerical-environment-qualified"
          wide
        >
          <RegimeStatement />
        </Exhibit>
      </main>

      <section className="ap-friction" aria-labelledby="ap-friction-title">
        <header className="ap-friction-head">
          <div>
            <div className="ap-label">FRICTION SENSITIVITY · INVERTED BACKTESTER</div>
            <h2 id="ap-friction-title">Gross luck under assumed turnover costs.</h2>
          </div>
          <strong>81-ticker training universe, nominal TRY.</strong>
        </header>
        <p className="ap-friction-copy">
          Equal-weight top-10 baskets use descending ranks inside each model and year; raw score magnitudes never cross model boundaries. Cost values are assumptions, not measured BIST costs. No bid–ask spread, market impact, liquidity, capacity, or tradeability is inferred.
        </p>
        <FrictionChart friction={report?.friction} reason={reason} />
        <p className="ap-finding">
          <strong>BOUNDARY · </strong>Gross and net bars are descriptive historical sensitivity outputs, not realizable returns or investment value. Nominal TRY is shown here; CPI-deflated TRY and USD-basis evidence remain separate. Multiplicity, power, survivorship, retrospective-cohort, single-regime, and environment limitations remain unchanged.
        </p>
        <SourceLine limitation="assumed bps only; no execution, spread, impact, liquidity, or tradeability inputs">{SOURCE.friction}</SourceLine>
      </section>

      <footer className="ap-limitations">
        <strong>LIMITATIONS HELD IN VIEW</strong>
        <span>multiple-comparison correction · three test years · 81-ticker training universe, n=80/split · retrospectively fixed cohort · unresolved survivorship risk · nominal TRY · one macro regime · environment-qualified numerical reproduction</span>
      </footer>
    </div>
  )
}

const CSS = `
.ap {
  --ap-ink: #090d0c; --ap-paper: #e8ece6; --ap-dim: #9caaa0; --ap-faint: #65736a;
  --ap-emerald: #4da583; --ap-gold: #c8a35a; --ap-copper: #a8674b;
  position: relative; margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px)); padding: 36px clamp(22px, 3vw, 52px) 90px;
  color: var(--ap-paper); overflow: hidden;
  background: radial-gradient(900px 480px at 82% -8%, rgba(168,103,75,.1), transparent 62%),
    linear-gradient(160deg, #0c1110 0%, var(--ap-ink) 58%, #070a09 100%);
}
.ap * { box-sizing: border-box; }
.ap-grid { position: absolute; inset: 0; pointer-events: none; opacity: .3;
  background-image: linear-gradient(rgba(232,236,230,.025) 1px, transparent 1px), linear-gradient(90deg, rgba(232,236,230,.025) 1px, transparent 1px);
  background-size: 32px 32px; }
.ap > *:not(.ap-grid) { position: relative; z-index: 1; }
.ap-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 30px; flex-wrap: wrap; }
.ap-kicker, .ap-label, .ap-source, .ap-mode, .ap-number { font-family: var(--font-mono); }
.ap-kicker { color: var(--ap-copper); font-size: 10px; letter-spacing: .34em; margin-bottom: 12px; }
.ap-hero h1 { margin: 0 0 11px; font-size: clamp(28px, 4vw, 50px); line-height: 1; font-weight: 620; letter-spacing: -.025em; }
.ap-hero h1 em { color: var(--ap-copper); font-weight: 520; }
.ap-hero p { max-width: 72ch; margin: 0; color: var(--ap-dim); font-size: 13.5px; line-height: 1.65; }
.ap-mode { width: min(330px, 100%); border: 1px solid rgba(200,211,202,.18); border-left: 3px solid var(--ap-emerald); background: rgba(10,15,13,.8); padding: 13px 15px; display: grid; gap: 6px; }
.ap-mode.is-fallback { border-left-color: var(--ap-copper); }
.ap-mode > span { color: var(--ap-emerald); font-size: 9px; letter-spacing: .2em; }
.ap-mode.is-fallback > span { color: var(--ap-copper); }
.ap-mode > strong { color: var(--ap-dim); font-size: 10px; line-height: 1.45; font-weight: 500; }
.ap-caveat { margin: 25px 0; max-width: 1180px; border: 1px solid rgba(200,163,90,.38); border-left: 3px solid var(--ap-gold); background: rgba(17,18,14,.75); padding: 13px 16px; color: var(--ap-paper); font-size: 12.5px; line-height: 1.65; }
.ap-caveat strong { color: var(--ap-gold); }
.ap-exhibits { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; max-width: 1220px; }
.ap-exhibit { border: 1px solid rgba(200,211,202,.16); border-top: 2px solid rgba(77,165,131,.55); background: rgba(10,15,13,.72); padding: 18px; min-width: 0; }
.ap-exhibit.is-wide { grid-column: 1 / -1; }
.ap-exhibit-head { display: flex; align-items: flex-start; gap: 14px; }
.ap-number { color: var(--ap-faint); font-size: 25px; line-height: 1; }
.ap-label { color: var(--ap-emerald); font-size: 9px; letter-spacing: .25em; }
.ap-exhibit h2 { margin: 5px 0 0; font-size: 18px; line-height: 1.25; font-weight: 600; }
.ap-chart { margin: 16px 0; min-height: 150px; }
.ap-finding { margin: 0; color: var(--ap-dim); font-size: 12px; line-height: 1.65; }
.ap-finding strong { color: var(--ap-paper); font-family: var(--font-mono); font-size: 9px; letter-spacing: .12em; }
.ap-source { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 7px 18px; margin-top: 14px; padding-top: 10px; border-top: 1px dashed rgba(200,211,202,.13); color: var(--ap-faint); font-size: 8.5px; line-height: 1.5; letter-spacing: .04em; }
.ap-empty { min-height: 150px; border: 1px dashed rgba(168,103,75,.5); display: grid; place-content: center; gap: 8px; text-align: center; padding: 20px; }
.ap-empty strong { color: var(--ap-copper); font-family: var(--font-mono); font-size: 9px; letter-spacing: .16em; }
.ap-empty span { color: var(--ap-faint); font-size: 11px; }
.ap-instability { font-family: var(--font-mono); font-size: 9px; }
.ap-instability-head, .ap-instability-row { display: grid; grid-template-columns: minmax(190px, 1.7fr) repeat(3, minmax(66px, .55fr)); gap: 8px; align-items: center; }
.ap-instability-head { color: var(--ap-faint); letter-spacing: .13em; padding: 0 8px 7px; }
.ap-instability-row { border-top: 1px solid rgba(200,211,202,.09); padding: 7px 8px; color: var(--ap-dim); }
.ap-instability-row > span:not(:first-child) { text-align: right; padding: 4px 6px; }
.ap-instability-row .is-positive { color: var(--ap-emerald); background: rgba(77,165,131,.08); }
.ap-instability-row .is-negative { color: #cb8162; background: rgba(168,103,75,.1); }
.ap-overfit-row { display: grid; grid-template-columns: minmax(150px, 1.2fr) minmax(120px, 1fr) 52px; gap: 9px; align-items: center; margin: 8px 0; font-family: var(--font-mono); font-size: 8.5px; color: var(--ap-dim); }
.ap-overfit-row strong { text-align: right; color: var(--ap-paper); }
.ap-ic-track { height: 10px; position: relative; background: rgba(232,236,230,.035); }
.ap-zero { position: absolute; left: 50%; top: -2px; bottom: -2px; width: 1px; background: rgba(232,236,230,.35); }
.ap-ic-bar { position: absolute; top: 2px; height: 6px; background: var(--ap-emerald); }
.ap-ic-bar.is-negative { background: var(--ap-copper); }
.ap-axis { display: flex; justify-content: space-between; margin-left: 38%; color: var(--ap-faint); font: 8px var(--font-mono); }
.ap-sparsity-row { display: grid; grid-template-columns: 52px minmax(90px, 1fr) 48px; gap: 8px; align-items: center; margin: 15px 0; font: 9px var(--font-mono); color: var(--ap-dim); }
.ap-sparsity-row small { grid-column: 2 / -1; color: var(--ap-faint); }
.ap-count-track, .ap-p-track, .ap-power-track { height: 12px; background: rgba(232,236,230,.05); overflow: hidden; }
.ap-count-track span { display: block; height: 100%; background: linear-gradient(90deg, rgba(77,165,131,.35), var(--ap-emerald)); }
.ap-significance { border: 1px solid rgba(200,211,202,.1); padding: 13px; }
.ap-sig-ic { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 15px; font: 9px var(--font-mono); color: var(--ap-faint); }
.ap-sig-ic strong { font-size: 24px; color: var(--ap-copper); }
.ap-p-row { display: grid; grid-template-columns: 150px 1fr 54px; gap: 8px; align-items: center; margin: 10px 0; font: 8.5px var(--font-mono); color: var(--ap-dim); }
.ap-p-row strong { text-align: right; color: var(--ap-paper); }
.ap-p-track span { display: block; min-width: 3px; height: 100%; background: var(--ap-gold); }
.ap-alpha { margin-top: 12px; color: var(--ap-faint); font: 8.5px var(--font-mono); text-align: right; }
.ap-power-row { display: grid; grid-template-columns: 140px 1fr 76px; gap: 8px; align-items: center; margin: 16px 0; font: 8.5px var(--font-mono); color: var(--ap-dim); }
.ap-power-track span { display: block; height: 100%; background: linear-gradient(90deg, var(--ap-gold), var(--ap-copper)); }
.ap-power-row strong { text-align: right; color: var(--ap-paper); }
.ap-power-row small { grid-column: 2 / -1; color: var(--ap-faint); }
.ap-regime { min-height: 150px; display: grid; place-content: center; gap: 12px; text-align: center; padding: 18px; border: 1px solid rgba(200,163,90,.25); font-family: var(--font-mono); }
.ap-regime strong { color: var(--ap-copper); font-size: 11px; letter-spacing: .2em; }
.ap-regime p { margin: 0; color: var(--ap-dim); font-size: 10px; }
.ap-regime small { color: var(--ap-faint); font-size: 8.5px; }
.ap-friction { margin-top: 20px; max-width: 1220px; border: 1px solid rgba(200,163,90,.3); border-top: 2px solid var(--ap-gold); background: rgba(10,15,13,.78); padding: 20px; }
.ap-friction-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; flex-wrap: wrap; }
.ap-friction-head h2 { margin: 5px 0 0; font-size: 21px; font-weight: 600; }
.ap-friction-head > strong { color: var(--ap-gold); font: 9px var(--font-mono); letter-spacing: .08em; }
.ap-friction-copy { max-width: 100ch; color: var(--ap-dim); font-size: 12px; line-height: 1.65; }
.ap-friction-viz { margin: 16px 0; }
.ap-friction-controls { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
.ap-friction-controls label { display: grid; gap: 5px; color: var(--ap-faint); font: 8px var(--font-mono); letter-spacing: .12em; }
.ap-friction-controls select { min-width: 210px; border: 1px solid rgba(200,211,202,.2); background: #0b100e; color: var(--ap-paper); padding: 8px 10px; font: 10px var(--font-mono); }
.ap-cost-controls { display: flex; gap: 6px; flex-wrap: wrap; }
.ap-cost-controls button { border: 1px solid rgba(200,211,202,.18); background: rgba(232,236,230,.03); color: var(--ap-dim); padding: 7px 10px; font: 8.5px var(--font-mono); cursor: pointer; }
.ap-cost-controls button.is-active { border-color: var(--ap-gold); color: var(--ap-gold); background: rgba(200,163,90,.08); }
.ap-friction-svg { display: block; width: 100%; min-height: 260px; border: 1px solid rgba(200,211,202,.12); }
.ap-friction-bg { fill: #080c0a; }
.ap-friction-zero { stroke: rgba(232,236,230,.3); stroke-width: 1; stroke-dasharray: 3 4; }
.ap-friction-axis-label, .ap-friction-value, .ap-friction-year, .ap-friction-turnover, .ap-friction-legend { fill: var(--ap-dim); font: 9px var(--font-mono); }
.ap-friction-value { fill: var(--ap-paper); }
.ap-friction-year { fill: var(--ap-gold); font-size: 11px; }
.ap-friction-turnover { fill: var(--ap-faint); font-size: 8px; }
.ap-friction-bar.is-gross { fill: var(--ap-emerald); }
.ap-friction-bar.is-net { fill: var(--ap-copper); }
.ap-friction-stamp { border: 1px solid rgba(200,163,90,.42); background: rgba(14,11,10,.96); color: var(--ap-gold); padding: 6px 9px; font: 9px/1.35 var(--font-mono); letter-spacing: .025em; }
.ap-friction-meta { display: flex; justify-content: space-between; gap: 8px 18px; flex-wrap: wrap; margin-top: 8px; color: var(--ap-faint); font: 8.5px var(--font-mono); }
.ap-limitations { margin-top: 20px; max-width: 1220px; border: 1px solid rgba(168,103,75,.35); background: rgba(14,11,10,.76); padding: 13px 16px; display: grid; gap: 7px; }
.ap-limitations strong { color: var(--ap-copper); font: 9px var(--font-mono); letter-spacing: .22em; }
.ap-limitations span { color: var(--ap-dim); font: 9px/1.6 var(--font-mono); }
@media (max-width: 900px) { .ap-exhibits { grid-template-columns: 1fr; } .ap-exhibit.is-wide { grid-column: auto; } }
@media (max-width: 620px) {
  .ap-instability-head, .ap-instability-row { grid-template-columns: minmax(115px, 1.4fr) repeat(3, 52px); }
  .ap-overfit-row { grid-template-columns: 130px 1fr 44px; }
  .ap-p-row, .ap-power-row { grid-template-columns: 1fr; }
  .ap-p-row strong, .ap-power-row strong { text-align: left; }
  .ap-power-row small { grid-column: auto; }
  .ap-friction { padding: 14px; }
  .ap-friction-svg { min-width: 760px; }
  .ap-friction-viz { overflow-x: auto; }
}
@media (prefers-reduced-motion: reduce) { .ap, .ap * { animation: none !important; transition: none !important; } }
`
