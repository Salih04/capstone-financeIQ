import { useEffect, useState } from 'react'
import { Database, Mail, ShieldCheck, Sparkles } from 'lucide-react'
import { Chip } from '../components/ui'
import { researchApi } from '../api/researchApi'
import {
  MetricCard, RenderList, WarningCallout, CollapsibleJson, EvidencePanel, SignalBadge, asText,
} from '../utils/safeRender'

const GROUP_LABEL = {
  balance_sheet: 'Balance-sheet features',
  growth: 'Growth features',
  other: 'Income & profitability features',
}

export default function DataQualityPage() {
  const [dq, setDq] = useState(null)
  const [summary, setSummary] = useState(null)
  const [evi, setEvi] = useState(null)

  useEffect(() => {
    researchApi.dataQuality().then(r => setDq(r.data))
    researchApi.summary().then(r => setSummary(r.data))
    researchApi.frozenEvidence().then(r => setEvi(r.data))
  }, [])

  const d = dq?.data_quality || {}
  const ctx = summary?.context || {}
  const groups = ctx.feature_groups || {}
  const bench = d.benchmark || {}
  const cy = d.corrected_yearly || {}
  const fv = d.free_valuation || {}
  const sd = d.source_distinction || {}
  const accCorrected = sd.accepted_corrected_yearly_columns || cy.accepted_columns || []
  const missingVal = sd.still_rejected_valuation_columns || cy.frozen_valuation_columns || []
  const mis2024 = sd.rejected_2024_misaligned_columns || cy.misalignment_2024_columns || []
  const bs2024 = sd.balance_2024_correction || {}
  const bs2024Fixed = bs2024.present && (bs2024.rows_corrected || 0) > 0
  const oldSnapshot = d.frozen_columns || ctx.rejected_frozen_columns || []
  const featureCount = ctx.feature_count

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <section style={styles.hero}>
        <div>
          <div style={styles.kicker}><Sparkles size={15} /> Integrity Dashboard</div>
          <h1 style={styles.title}>Data quality is the core strength of FinanceIQ.</h1>
          <p style={styles.subtitle}>
            This audit separates accepted year-varying features from rejected frozen snapshots, documents
            corrected yearly financials, and explains why leakage-safe modeling rejects future information.
          </p>
          <div style={styles.badges}>
            <SignalBadge tone="good"><ShieldCheck size={12} /> Leakage controls active</SignalBadge>
            <SignalBadge tone="good">{asText(featureCount)} validated features</SignalBadge>
            <SignalBadge tone={bench.excess_outperform_targets_enabled ? 'good' : 'warn'}>BIST100 {bench.excess_outperform_targets_enabled ? 'available' : 'missing'}</SignalBadge>
          </div>
        </div>
        <div style={styles.auditCard}>
          <Database size={22} color="var(--primary)" />
          <div style={styles.auditTitle}>Audit Rule</div>
          <p style={styles.auditText}>
            Green means accepted and used. Amber means useful but incomplete or requiring correction.
            Red is reserved for true rejected inputs such as frozen snapshots or leakage fields.
          </p>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(155px,1fr))', gap: 12 }}>
        <MetricCard label="Features used by model" value={asText(featureCount)} tone="good" sub="change year to year" />
        <MetricCard label="Newly accepted" value={asText(accCorrected.length)} tone="good" sub="corrected income/profit" />
        <MetricCard label="Still missing valuation" value={asText(missingVal.length)} tone="warn" sub="repeated snapshot" />
        <MetricCard label="2024 balance sheet" value={bs2024Fixed ? 'Corrected' : mis2024.length ? 'Issue detected' : 'OK'} tone={bs2024Fixed ? 'good' : mis2024.length ? 'warn' : 'good'} sub={bs2024Fixed ? `${bs2024.rows_corrected} rows fixed` : 'columns shifted'} />
        <MetricCard label="Market benchmark" value={bench.excess_outperform_targets_enabled ? 'Available' : 'Missing'} tone={bench.excess_outperform_targets_enabled ? 'good' : 'warn'} sub="BIST100" />
      </div>

      {/* Section A — validated features currently used */}
      <EvidencePanel title="A · Features the model uses today" sub="All known at the end of each year and genuinely change year to year" tone="good">
        {Object.entries(groups).map(([g, arr]) => (
          <div key={g}>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-3)', marginBottom: 5 }}>{GROUP_LABEL[g] || g} ({(arr || []).length})</div>
            <RenderList items={arr} color="success" empty="none" />
          </div>
        ))}
      </EvidencePanel>

      {/* Section B & D — corrected accepted vs still-missing valuation */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px,1fr))', gap: 16 }}>
        <EvidencePanel title="B · Corrected yearly columns accepted" tone="good"
          sub="Genuinely change year by year in the corrected files — now feed the model">
          <RenderList items={accCorrected} color="success" empty="none" />
          <p style={{ fontSize: 12, color: 'var(--text-3)', margin: 0, lineHeight: 1.5 }}>
            Real per-year income & profitability (revenue, EBITDA, net income, margins, ROE, ROA). These
            actually move over time, so the model can learn from them.
          </p>
        </EvidencePanel>

        <EvidencePanel title="D · Still missing: historical valuation" tone="warn"
          sub="Valuable in theory, but current files repeat the same snapshot">
          <RenderList items={missingVal} color="warning" empty="none" />
          <p style={{ fontSize: 12, color: 'var(--text-3)', margin: 0, lineHeight: 1.5 }}>
            P/E, P/B, EV/EBITDA, market cap and enterprise value are the same value copied into every year, so
            they carry no history and are rejected until real per-year values are supplied.
          </p>
        </EvidencePanel>
      </div>

      {/* Section C — old snapshot rejected + overlap note */}
      <EvidencePanel title="C · Old snapshot source rejected" tone="bad"
        sub="The earlier export repeated one value across years, so it was excluded">
        <RenderList items={oldSnapshot} color="danger" empty="none" />
        <WarningCallout title="Why some names appear twice" tone="info">
          {sd.source_note || 'Names like revenue, EBITDA and ROE appear as both rejected and accepted because the OLD snapshot repeated one value across years (rejected), while the CORRECTED yearly source genuinely changes year by year (accepted and now used by the model).'}
        </WarningCallout>
      </EvidencePanel>

      {/* Section E — 2024 balance sheet: corrected (green) or still-issue (amber) */}
      {bs2024Fixed ? (
        <EvidencePanel title="E · 2024 balance sheet corrected" tone="good"
          sub={`Manual correction applied for ${bs2024.rows_corrected} ticker(s) (corrected_balance_sheet_2024.csv)`}>
          <p style={{ fontSize: 12.5, color: 'var(--text-2)', margin: 0, lineHeight: 1.55 }}>
            The 2024 export had shifted balance-sheet columns. Real 2024 values were supplied manually
            (money as money, ratios as ratios) and override only the 2024 balance-sheet fields. P/B,
            enterprise value and EV/EBITDA for those tickers are recomputed from the corrected equity / net debt.
          </p>
          {(bs2024.tickers || []).length ? <RenderList items={bs2024.tickers} color="success" /> : null}
        </EvidencePanel>
      ) : mis2024.length > 0 ? (
        <EvidencePanel title="E · 2024 export alignment issue" tone="warn"
          sub="Some balance-sheet fields in the 2024 file appear shifted into the wrong columns">
          <RenderList items={mis2024} color="warning" empty="none" />
          <p style={{ fontSize: 12, color: 'var(--text-3)', margin: 0, lineHeight: 1.5 }}>
            Rather than guessing or filling these values, the affected 2024 cells were rejected. The model never
            sees shifted/misaligned numbers. Supply real 2024 values via
            <code> data/trusted_raw/financials/corrected_balance_sheet_2024.csv</code> to fix this.
          </p>
        </EvidencePanel>
      ) : null}

      {/* Free valuation builder status */}
      {fv.attempted && (
        <EvidencePanel title="F · Free valuation builder (no Fintables)" tone={(fv.columns_entering_candidate || []).length ? 'good' : 'info'}
          sub="Reconstruct P/E, P/B, EV/EBITDA from free price + shares + validated financials">
          <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, lineHeight: 1.6 }}>
            We do not need to buy frozen valuation data if we can calculate it ourselves:
            <b> market cap = year-end price × shares</b>, then P/E = market cap / net income, P/B = market cap / equity,
            EV/EBITDA = (market cap + net debt) / EBITDA.
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Chip color="success">Year-end price (Yahoo): {asText(fv.price_rows)}/{asText(fv.total_rows)} rows</Chip>
            <Chip color={fv.shares_status === 'manual' ? 'success' : 'warning'}>Shares outstanding: {asText(fv.shares_status)}</Chip>
          </div>
          {(fv.columns_entering_candidate || []).length ? (
            <div>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--success-light)', marginBottom: 5 }}>Derived columns now in the model</div>
              <RenderList items={fv.columns_entering_candidate} color="success" />
            </div>
          ) : (
            <WarningCallout title="Shares outstanding required (capital-event workflow)" tone="warn">
              Year-end prices are collected free from Yahoo, but historical <b>shares outstanding</b> are not.
              You no longer fill 240 rows — instead record only capital <b>changes</b> in
              <code> data/trusted_raw/shares_outstanding_events.csv</code> (one row per capital increase; stable
              capital = a single 2020 row), then run <code>make shares &amp;&amp; make valuation</code>. Use
              <b> total issued / paid-in shares</b> (share count when nominal value is 1 TL) — <b>never free float</b>
              (“Fiili Dolaşımdaki Pay Tutarı” understates total shares and is rejected). Then P/E, P/B and
              EV/EBITDA are computed and can enter the model.
            </WarningCallout>
          )}
        </EvidencePanel>
      )}

      {/* Message to data provider */}
      <EvidencePanel title="Message to data provider" tone="info"
        sub={<span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}><Mail size={12} /> Copy-ready complaint summary</span>}>
        <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6, margin: 0 }}>
          The supplied yearly and quarterly exports repeat one point-in-time snapshot of valuation,
          profitability and income for every period. We need <b>real per-year (or per-quarter) historical
          values</b> for these fields so the figures change over time. Without genuine history, leakage-safe
          modeling can only use balance-sheet and growth features, which alone show no reliable edge.
        </p>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
          <Chip color="success">Need: per-year income statement</Chip>
          <Chip color="success">Need: per-year valuation (P/E, P/B, EV/EBITDA)</Chip>
          <Chip color="success">Need: per-year profitability (ROE, ROA, margins)</Chip>
        </div>
      </EvidencePanel>

      {/* Leakage controls */}
      <EvidencePanel title="Leakage controls" tone="good">
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, lineHeight: 1.55 }}>{asText(d.leakage_controls)}</p>
        <p style={{ fontSize: 11.5, color: 'var(--text-3)', margin: 0 }}>
          Leakage = using information not available before the target year. <code>next_year_*</code>,
          <code> same_year_return_pct</code> and <code>target_year</code> can never be features.
        </p>
      </EvidencePanel>

      {/* Technical evidence (collapsed) */}
      <div>
        <CollapsibleJson label="Technical evidence (developer / jury detail)"
          value={{ source_distinction: sd, corrected_yearly: cy,
                   frozen_column_evidence: evi?.available ? evi.columns : 'not generated' }} />
      </div>
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
    background: 'linear-gradient(135deg, rgba(58,199,139,0.13), rgba(244,176,74,0.08) 44%, var(--surface-2))',
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
  auditCard: {
    background: 'rgba(8,15,26,0.54)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: 18,
    display: 'flex',
    flexDirection: 'column',
    gap: 9,
  },
  auditTitle: {
    color: 'var(--text-1)',
    fontSize: 18,
    fontWeight: 900,
  },
  auditText: {
    color: 'var(--text-2)',
    fontSize: 12.8,
    lineHeight: 1.6,
    margin: 0,
  },
}
