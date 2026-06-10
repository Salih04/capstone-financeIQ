import { useEffect, useMemo, useState } from 'react'

// ---------------------------------------------------------------------------
// AI Research Assistant — a research query instrument, not a chat.
// Left: intent tuner. Center: results crystallize from noise per query.
// Right: Signal Readout reacting to hover. Mock data; API wiring comes later.
// ---------------------------------------------------------------------------

const RESEARCH_MOCK = {
  activeIntent: 'TOP_RANKED',
  query_resolved_in_ms: 340,
  results: [
    {
      ticker: 'ASELS', rank: 1,
      hybrid_score: 78.4,
      ml_score: 0.81, confidence: 0.74, llm_score: 0.68,
      coverage: 0.94,
      top_features: ['ROE', 'FCF_margin', 'revenue_growth'],
      verdict: 'Strong ranking signal — low predictive certainty',
      inference_only: false,
    },
    {
      ticker: 'THYAO', rank: 2,
      hybrid_score: 71.2,
      ml_score: 0.68, confidence: 0.79, llm_score: 0.61,
      coverage: 0.97,
      top_features: ['operating_margin', 'asset_turnover', 'net_debt_ebitda'],
      verdict: 'Strong ranking signal — low predictive certainty',
      inference_only: false,
    },
    {
      ticker: 'EREGL', rank: 3,
      hybrid_score: 69.8,
      ml_score: 0.72, confidence: 0.65, llm_score: 0.55,
      coverage: 0.89,
      top_features: ['pb_ratio', 'ebitda_margin', 'working_capital'],
      verdict: 'Moderate signal — data gaps present',
      inference_only: false,
    },
    {
      ticker: 'SISE', rank: 4,
      hybrid_score: 65.1,
      ml_score: 0.61, confidence: 0.71, llm_score: 0.49,
      coverage: 0.92,
      top_features: ['current_ratio', 'equity_growth', 'gross_margin'],
      verdict: 'Moderate signal',
      inference_only: false,
    },
    {
      ticker: 'TTKOM', rank: 8,
      hybrid_score: 28.1,
      ml_score: 0.24, confidence: 0.31, llm_score: 0.21,
      coverage: 0.61,
      top_features: ['leverage_ratio', 'net_debt_ebitda'],
      verdict: 'Weak signal — partial coverage',
      inference_only: false,
    },
    {
      ticker: 'SMRTG', rank: 9,
      hybrid_score: 19.3,
      ml_score: 0.17, confidence: 0.22, llm_score: null,
      coverage: 0.38,
      top_features: ['current_ratio'],
      verdict: 'Insufficient data — use with caution',
      inference_only: true,
    },
  ],
  system_note: 'Walk-forward IC ≈ 0. Rankings reflect historical patterns only.',
  hybrid_weights: { ml: 0.65, confidence: 0.2, llm: 0.15 },
}

const INTENTS = [
  {
    key: 'BENCHMARK_OUTPERFORMERS',
    label: 'BENCHMARK OUTPERFORMERS',
    desc: 'beat BIST100 in T+1 · historical evaluation',
    ms: 412,
    subtitle: 'Tickers whose realized T+1 return exceeded BIST100, 2020–2024. Historical fact, not a forecast.',
    select: (rs) => rs.filter((r) => r.hybrid_score >= 50),
  },
  {
    key: 'TOP_RANKED',
    label: 'TOP RANKED',
    desc: 'highest composite research score',
    ms: 340,
    subtitle: 'Composite diagnostic ranking across the validated universe. Ranking signal, not predictive certainty.',
    select: (rs) => [...rs].sort((a, b) => a.rank - b.rank),
  },
  {
    key: 'DATA_QUALITY',
    label: 'DATA QUALITY',
    desc: 'coverage & feature completeness',
    ms: 287,
    subtitle: 'Universe ordered by validated feature coverage. Grainy entries carry thin data by design.',
    select: (rs) => [...rs].sort((a, b) => b.coverage - a.coverage),
  },
  {
    key: 'VALUATION_SCREEN',
    label: 'VALUATION SCREEN',
    desc: 'P/E · P/B · EV/EBITDA ranked',
    ms: 365,
    subtitle: 'Valuation-feature composite from validated year-end inputs only. Frozen snapshots are excluded.',
    select: (rs) => [...rs].sort((a, b) => b.ml_score - a.ml_score),
  },
  {
    key: 'DIAGNOSTICS',
    label: 'DIAGNOSTICS',
    desc: 'model health · IC · contributions',
    ms: 198,
    subtitle: 'Model health view. Walk-forward IC ≈ 0 across 2020–2024 — the instrument reports its own weakness.',
    select: (rs) => [...rs].sort((a, b) => b.ml_score - a.ml_score),
  },
]

const W = RESEARCH_MOCK.hybrid_weights

function scoreColor(score) {
  if (score >= 60) return 'var(--ra-emerald)'
  if (score >= 40) return 'var(--ra-gold)'
  return 'var(--ra-copper)'
}

// LLM missing → its weight folds back into ML + Confidence, proportionally.
function effectiveWeights(r) {
  if (r.llm_score != null) return { ml: W.ml, confidence: W.confidence, llm: W.llm, redistributed: false }
  const base = W.ml + W.confidence
  return { ml: W.ml / base, confidence: W.confidence / base, llm: 0, redistributed: true }
}

function ScopeBar({ label, weight, value, color }) {
  return (
    <div className="ra-bar">
      <span className="ra-bar-label">{label}</span>
      <span className="ra-bar-weight">×{weight.toFixed(2)}</span>
      <span className="ra-bar-track">
        {value == null
          ? <span className="ra-bar-null">NO DATA</span>
          : <span className="ra-bar-fill" style={{ width: `${value * 100}%`, background: color }} />}
      </span>
      <span className="ra-bar-val">{value == null ? '—' : value.toFixed(2)}</span>
    </div>
  )
}

function SignalReadout({ r }) {
  if (!r) {
    return (
      <aside className="ra-readout" key="resting" aria-live="polite">
        <div className="ra-readout-kicker">SIGNAL READOUT · SYSTEM STATUS</div>
        <div className="ra-readout-sub" style={{ marginTop: 0 }}>HYBRID WEIGHTS</div>
        <ScopeBar label="ML" weight={W.ml} value={W.ml} color="var(--ra-emerald)" />
        <ScopeBar label="CONFIDENCE" weight={W.confidence} value={W.confidence} color="var(--ra-gold)" />
        <ScopeBar label="LLM" weight={W.llm} value={W.llm} color="var(--ra-copper)" />
        <div className="ra-flag">WALK-FORWARD IC ≈ 0</div>
        <p className="ra-verdict">
          Rankings reflect historical patterns only. Hover a result to open its full breakdown.
        </p>
      </aside>
    )
  }
  const w = effectiveWeights(r)
  const color = scoreColor(r.hybrid_score)
  return (
    <aside className="ra-readout" key={r.ticker} aria-live="polite">
      <div className="ra-readout-kicker">SIGNAL READOUT</div>
      <div className="ra-readout-head">
        <span className="ra-readout-ticker">{r.ticker}</span>
        <span className="ra-readout-rank">RANK #{r.rank}</span>
      </div>
      <div className="ra-readout-score">
        <span style={{ color }}>{r.hybrid_score.toFixed(1)}</span>
        <em>hybrid diagnostic score / 100</em>
      </div>

      <ScopeBar label="ML" weight={w.ml} value={r.ml_score} color="var(--ra-emerald)" />
      <ScopeBar label="CONFIDENCE" weight={w.confidence} value={r.confidence} color="var(--ra-gold)" />
      <ScopeBar label="LLM" weight={r.llm_score == null ? W.llm : w.llm} value={r.llm_score} color="var(--ra-copper)" />

      {w.redistributed && (
        <p className="ra-readout-redistribute">
          LLM evidence unavailable — its 0.15 weight is redistributed:
          ML ×{w.ml.toFixed(2)} · Confidence ×{w.confidence.toFixed(2)}.
        </p>
      )}

      <div className="ra-readout-sub">TOP FEATURES</div>
      <div className="ra-readout-features">
        {r.top_features.map((f) => <span key={f} className="ra-feature">{f}</span>)}
      </div>

      <div className="ra-readout-sub">COVERAGE</div>
      <div className="ra-coverage">
        <span className="ra-coverage-track">
          <span className="ra-coverage-fill" style={{ width: `${r.coverage * 100}%` }} />
        </span>
        <span className="ra-coverage-val">{Math.round(r.coverage * 100)}%</span>
      </div>

      {r.inference_only && <div className="ra-flag">INFERENCE-ONLY · NO REALIZED T+1 OUTCOME</div>}

      <p className="ra-verdict">{r.verdict}</p>
    </aside>
  )
}

export default function AIResearchAssistantPage() {
  const reduceMotion = useMemo(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  )
  const [intentKey, setIntentKey] = useState(RESEARCH_MOCK.activeIntent)
  const [phase, setPhase] = useState(reduceMotion ? 'ready' : 'resolving')
  const [hovered, setHovered] = useState(null)

  const intent = INTENTS.find((i) => i.key === intentKey)
  const results = useMemo(() => intent.select(RESEARCH_MOCK.results), [intent])
  const active = results.find((r) => r.ticker === hovered) || null

  useEffect(() => {
    if (reduceMotion) { setPhase('ready'); return undefined }
    setPhase('resolving')
    const id = setTimeout(() => setPhase('ready'), 520)
    return () => clearTimeout(id)
  }, [intentKey, reduceMotion])

  const selectIntent = (key) => {
    if (key === intentKey) return
    setHovered(null)
    setIntentKey(key)
  }

  return (
    <div className="ra">
      <style>{CSS}</style>
      <div className="ra-scan" aria-hidden="true" />

      <header className="ra-head">
        <div>
          <div className="ra-kicker">FINANCEIQ · RESEARCH QUERY INSTRUMENT</div>
          <h1>Query the signal. <em>Distrust the answer.</em></h1>
          <p>
            Queries resolve against validated project data only. The instrument surfaces ranking
            signal, explains it, and flags its own limitations. It does not advise.
          </p>
        </div>
        <div className="ra-formula">
          <div className="ra-formula-line">Hybrid score = 0.65 · ML + 0.20 · Confidence + 0.15 · LLM evidence</div>
          <div className="ra-formula-note">{RESEARCH_MOCK.system_note}</div>
        </div>
      </header>

      <div className="ra-grid">
        {/* ── Intent tuner ─────────────────────────────── */}
        <nav className="ra-tuner" aria-label="Query intent">
          <div className="ra-tuner-label">QUERY SCOPE</div>
          {INTENTS.map((i) => {
            const on = i.key === intentKey
            return (
              <button
                key={i.key}
                type="button"
                className={`ra-intent ${on ? 'is-on' : ''}`}
                aria-pressed={on}
                onClick={() => selectIntent(i.key)}
              >
                <span className="ra-intent-lamp" />
                <span className="ra-intent-text">
                  <span className="ra-intent-name">{i.label}</span>
                  <span className="ra-intent-desc">{i.desc}</span>
                </span>
              </button>
            )
          })}
        </nav>

        {/* ── Results field ───────────────────────────── */}
        <main className="ra-field">
          <div className="ra-field-head">
            <div>
              <div className="ra-field-title">{intent.label}</div>
              <div className="ra-field-sub">{intent.subtitle}</div>
            </div>
            <div className="ra-resolved">
              <span className={`ra-resolved-dot ${phase === 'resolving' ? 'is-busy' : ''}`} />
              {phase === 'resolving' ? 'resolving…' : `resolved in ${intent.ms}ms`}
            </div>
          </div>

          <div className={`ra-results ${phase}`}>
            <div className="ra-noise" aria-hidden="true" />
            {phase === 'ready' && results.map((r, i) => {
              const color = scoreColor(r.hybrid_score)
              const isActive = active?.ticker === r.ticker
              const grainy = r.coverage < 0.55
              return (
                <button
                  key={r.ticker}
                  type="button"
                  className={`ra-row ${isActive ? 'is-active' : ''} ${grainy ? 'is-grainy' : ''}`}
                  style={{ animationDelay: `${i * 0.07}s` }}
                  onMouseEnter={() => setHovered(r.ticker)}
                  onFocus={() => setHovered(r.ticker)}
                >
                  <span className="ra-row-rank">#{r.rank}</span>
                  <span className="ra-row-ticker">{r.ticker}</span>
                  <span className="ra-row-trace">
                    <span className="ra-row-fill" style={{ width: `${r.hybrid_score}%`, background: color }} />
                  </span>
                  <span className="ra-row-score" style={{ color }}>{r.hybrid_score.toFixed(1)}</span>
                  <span className="ra-row-cov">{Math.round(r.coverage * 100)}% cov</span>
                </button>
              )
            })}
          </div>
        </main>

        <SignalReadout r={phase === 'ready' ? active : null} />
      </div>

      <footer className="ra-caveat">
        <span className="ra-caveat-pulse" aria-hidden="true" />
        Hybrid score = 0.65 · ML + 0.20 · Confidence + 0.15 · LLM evidence
        <span className="ra-caveat-sep">·</span>
        Walk-forward IC ≈ 0 · Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.ra {
  --ra-ink: #0a0e0d;
  --ra-paper: #e8ece6;
  --ra-dim: #9fae9f;
  --ra-faint: #6b7a70;
  --ra-emerald: #4da583;
  --ra-gold: #c8a35a;
  --ra-copper: #a8674b;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.07), transparent 60%),
    radial-gradient(800px 500px at 8% 108%, rgba(168,103,75,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--ra-ink) 55%, #080b0a 100%);
  color: var(--ra-paper);
  overflow: hidden;
}
.ra * { box-sizing: border-box; }
.ra-scan {
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px);
}
.ra > *:not(.ra-scan) { position: relative; z-index: 2; }

/* ── header ── */
.ra-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 36px; flex-wrap: wrap; margin-bottom: 28px; }
.ra-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--ra-faint); margin-bottom: 13px; }
.ra-head h1 { margin: 0 0 10px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.ra-head h1 em { font-style: italic; color: var(--ra-emerald); }
.ra-head p { margin: 0; max-width: 56ch; color: var(--ra-dim); font-size: 14px; line-height: 1.55; }
.ra-formula {
  border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--ra-gold);
  background: rgba(14,20,19,0.72); padding: 14px 16px; max-width: 380px;
}
.ra-formula-line { font-family: var(--font-mono); font-size: 11.5px; color: var(--ra-paper); letter-spacing: 0.02em; }
.ra-formula-note { font-family: var(--font-mono); font-size: 10.5px; color: var(--ra-gold); margin-top: 8px; letter-spacing: 0.04em; }

/* ── grid ── */
.ra-grid { display: grid; grid-template-columns: 270px 1fr 320px; gap: 24px; align-items: start; }
@media (max-width: 1100px) { .ra-grid { grid-template-columns: 1fr; } }

/* ── intent tuner ── */
.ra-tuner { display: flex; flex-direction: column; gap: 8px; }
.ra-tuner-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.3em; color: var(--ra-faint); margin-bottom: 4px; }
.ra-intent {
  display: flex; align-items: center; gap: 12px; text-align: left;
  padding: 13px 14px; border: 1px solid rgba(200,211,202,0.16); border-radius: 3px;
  background: rgba(14,20,19,0.6); color: inherit; font: inherit; cursor: pointer;
  transition: border-color 0.18s, background 0.18s, box-shadow 0.18s, transform 0.1s;
}
.ra-intent:hover { border-color: rgba(200,163,90,0.45); box-shadow: 0 0 16px rgba(200,163,90,0.12); }
.ra-intent:active { transform: translateY(1px); }
.ra-intent:focus-visible { outline: 1px solid var(--ra-gold); outline-offset: 2px; }
.ra-intent.is-on {
  border-color: var(--ra-gold); background: rgba(22,29,27,0.9);
  box-shadow: inset 3px 0 0 var(--ra-gold), 0 0 18px rgba(200,163,90,0.12);
}
.ra-intent-lamp {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  background: rgba(200,211,202,0.2); transition: background 0.2s, box-shadow 0.2s;
}
.ra-intent.is-on .ra-intent-lamp { background: var(--ra-gold); box-shadow: 0 0 8px rgba(200,163,90,0.8); }
.ra-intent-name { display: block; font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.14em; color: var(--ra-paper); }
.ra-intent-desc { display: block; font-size: 10.5px; color: var(--ra-faint); margin-top: 3px; letter-spacing: 0.02em; }

/* ── results field ── */
.ra-field {
  border: 1px solid rgba(200,211,202,0.16); border-radius: 3px;
  background: rgba(11,16,15,0.6); padding: 18px 20px 20px; min-height: 420px;
}
.ra-field-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; flex-wrap: wrap; margin-bottom: 16px; }
.ra-field-title { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.26em; color: var(--ra-paper); }
.ra-field-sub { font-size: 12px; color: var(--ra-faint); margin-top: 6px; max-width: 52ch; line-height: 1.5; }
.ra-resolved { font-family: var(--font-mono); font-size: 10.5px; color: var(--ra-dim); display: flex; align-items: center; gap: 7px; white-space: nowrap; }
.ra-resolved-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ra-emerald); }
.ra-resolved-dot.is-busy { background: var(--ra-gold); animation: raPulse 0.5s ease-in-out infinite; }

.ra-results { position: relative; display: flex; flex-direction: column; gap: 6px; min-height: 320px; }
.ra-noise {
  position: absolute; inset: 0; pointer-events: none; opacity: 0; border-radius: 2px;
  background:
    repeating-linear-gradient(0deg, rgba(232,236,230,0.05) 0 1px, transparent 1px 3px),
    repeating-linear-gradient(90deg, rgba(232,236,230,0.03) 0 2px, transparent 2px 5px);
  transition: opacity 0.25s;
}
.ra-results.resolving .ra-noise { opacity: 1; animation: raStatic 0.18s steps(3) infinite; }

.ra-row {
  display: grid; grid-template-columns: 40px 70px 1fr 56px 72px; gap: 12px; align-items: center;
  padding: 11px 14px; border: 1px solid rgba(200,211,202,0.12); border-radius: 2px;
  background: rgba(14,20,19,0.55); color: inherit; font: inherit; text-align: left; cursor: pointer;
  opacity: 0; animation: raCrystal 0.5s ease forwards;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
}
.ra-row:hover, .ra-row:focus-visible { border-color: rgba(77,165,131,0.5); background: rgba(18,26,24,0.8); outline: none; }
.ra-row.is-active { border-color: var(--ra-emerald); box-shadow: inset 3px 0 0 var(--ra-emerald); }
.ra-row.is-grainy {
  background-image: repeating-linear-gradient(0deg, rgba(232,236,230,0.025) 0 1px, transparent 1px 3px);
  border-style: dashed;
}
.ra-row.is-grainy .ra-row-ticker { color: var(--ra-dim); }
.ra-row.is-grainy .ra-row-trace { border: 1px dashed rgba(200,211,202,0.25); }
.ra-row-rank { font-family: var(--font-mono); font-size: 11px; color: var(--ra-faint); }
.ra-row-ticker { font-family: var(--font-mono); font-size: 13px; font-weight: 700; letter-spacing: 0.06em; }
.ra-row-trace { position: relative; height: 9px; background: rgba(200,211,202,0.07); border-radius: 1px; overflow: hidden; }
.ra-row-fill { display: block; height: 100%; border-radius: 1px; transition: width 0.6s ease; }
.ra-row-score { font-family: var(--font-mono); font-size: 12.5px; font-weight: 700; text-align: right; }
.ra-row-cov { font-family: var(--font-mono); font-size: 10px; color: var(--ra-faint); text-align: right; letter-spacing: 0.04em; }

/* ── signal readout ── */
.ra-readout {
  border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--ra-emerald);
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85));
  padding: 18px 20px; border-radius: 3px; animation: raCrystal 0.4s ease;
}
.ra-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--ra-faint); margin-bottom: 12px; }
.ra-readout-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.ra-readout-ticker { font-family: var(--font-mono); font-size: 26px; font-weight: 700; letter-spacing: 0.04em; }
.ra-readout-rank { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.2em; color: var(--ra-gold); }
.ra-readout-score { margin: 10px 0 16px; display: flex; flex-direction: column; gap: 2px; }
.ra-readout-score span { font-family: var(--font-mono); font-size: 38px; line-height: 1; }
.ra-readout-score em { font-style: normal; font-size: 10px; letter-spacing: 0.16em; color: var(--ra-faint); text-transform: uppercase; }

.ra-bar { display: grid; grid-template-columns: 78px 38px 1fr 36px; gap: 8px; align-items: center; margin-bottom: 8px; font-family: var(--font-mono); }
.ra-bar-label { font-size: 9.5px; letter-spacing: 0.14em; color: var(--ra-dim); }
.ra-bar-weight { font-size: 9.5px; color: var(--ra-faint); }
.ra-bar-track { position: relative; height: 6px; background: rgba(200,211,202,0.09); border-radius: 1px; overflow: hidden; }
.ra-bar-fill { display: block; height: 100%; transition: width 0.5s ease; }
.ra-bar-null { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 7.5px; letter-spacing: 0.2em; color: var(--ra-copper); border: 1px dashed rgba(168,103,75,0.5); }
.ra-bar-val { font-size: 10.5px; text-align: right; color: var(--ra-paper); }

.ra-readout-redistribute {
  margin: 10px 0 0; font-size: 11px; line-height: 1.5; color: var(--ra-copper);
  border: 1px dashed rgba(168,103,75,0.45); border-radius: 2px; padding: 8px 10px;
}
.ra-readout-sub { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.26em; color: var(--ra-faint); margin: 16px 0 7px; }
.ra-readout-features { display: flex; flex-wrap: wrap; gap: 6px; }
.ra-feature {
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.03em;
  border: 1px solid rgba(200,211,202,0.2); border-radius: 2px; padding: 3px 8px; color: var(--ra-dim);
}
.ra-coverage { display: flex; align-items: center; gap: 10px; }
.ra-coverage-track { flex: 1; height: 6px; background: rgba(200,211,202,0.09); border-radius: 1px; overflow: hidden; }
.ra-coverage-fill { display: block; height: 100%; background: var(--ra-emerald); transition: width 0.5s ease; }
.ra-coverage-val { font-family: var(--font-mono); font-size: 11px; color: var(--ra-paper); }
.ra-flag {
  margin-top: 14px; font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.18em;
  color: var(--ra-gold); border: 1px solid rgba(200,163,90,0.45); border-radius: 2px; padding: 6px 9px;
}
.ra-verdict { margin: 14px 0 0; font-size: 12.5px; line-height: 1.55; color: var(--ra-dim); border-top: 1px dashed rgba(200,211,202,0.18); padding-top: 12px; }

/* ── caveat ── */
.ra-caveat {
  position: sticky; bottom: 14px; z-index: 4; margin-top: 32px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em; flex-wrap: wrap;
  color: var(--ra-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}
.ra-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--ra-gold); animation: raPulse 2.2s ease-in-out infinite; flex-shrink: 0; }
.ra-caveat-sep { color: var(--ra-faint); }

@keyframes raCrystal { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes raPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@keyframes raStatic { 0% { transform: translateY(0); } 50% { transform: translateY(1px); } 100% { transform: translateY(-1px); } }

@media (prefers-reduced-motion: reduce) {
  .ra *, .ra *::before, .ra *::after { animation: none !important; transition: none !important; }
  .ra-row, .ra-row.is-grainy { opacity: 1; }
}
`
