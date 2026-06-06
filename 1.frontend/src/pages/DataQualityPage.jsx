import { useEffect, useState } from 'react'
import { Database, Mail } from 'lucide-react'
import { SectionHeader, Chip } from '../components/ui'
import { researchApi } from '../api/researchApi'
import {
  MetricCard, RenderList, WarningCallout, CollapsibleJson, EvidencePanel, Bullets, asText,
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
  const oldSnapshot = d.frozen_columns || ctx.rejected_frozen_columns || []
  const featureCount = ctx.feature_count

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <SectionHeader title="Data Quality & Integrity" sub="Which financial data the model uses, and why — for stakeholders and the data provider" icon={Database} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(155px,1fr))', gap: 12 }}>
        <MetricCard label="Features used by model" value={asText(featureCount)} tone="good" sub="change year to year" />
        <MetricCard label="Newly accepted" value={asText(accCorrected.length)} tone="good" sub="corrected income/profit" />
        <MetricCard label="Still missing valuation" value={asText(missingVal.length)} tone="warn" sub="repeated snapshot" />
        <MetricCard label="2024 file issue" value={mis2024.length ? 'Detected' : 'None'} tone={mis2024.length ? 'warn' : 'good'} sub="columns shifted" />
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

      {/* Section E — 2024 file issue */}
      {mis2024.length > 0 && (
        <EvidencePanel title="E · 2024 export alignment issue" tone="warn"
          sub="Some balance-sheet fields in the 2024 file appear shifted into the wrong columns">
          <RenderList items={mis2024} color="warning" empty="none" />
          <p style={{ fontSize: 12, color: 'var(--text-3)', margin: 0, lineHeight: 1.5 }}>
            Rather than guessing or filling these values, the affected 2024 cells were rejected. The model never
            sees shifted/misaligned numbers.
          </p>
        </EvidencePanel>
      )}

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
