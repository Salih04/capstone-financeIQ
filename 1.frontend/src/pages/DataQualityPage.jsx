import { useEffect, useState } from 'react'
import { Database, Mail } from 'lucide-react'
import { SectionHeader, Chip } from '../components/ui'
import { researchApi } from '../api/researchApi'
import {
  MetricCard, RenderList, WarningCallout, CollapsibleJson, EvidencePanel, Bullets, asText,
} from '../utils/safeRender'

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
  const frozen = d.frozen_columns || ctx.rejected_frozen_columns || []
  const misaligned = d.misaligned_columns || []
  const bench = d.benchmark || {}
  const cy = d.corrected_yearly || {}
  const acceptedCount = Object.values(groups).reduce((a, arr) => a + (arr || []).length, 0) || ctx.feature_count

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <SectionHeader title="Data Quality & Integrity" sub="Why each column is accepted or rejected — capstone jury & data-provider evidence" icon={Database} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(155px,1fr))', gap: 12 }}>
        <MetricCard label="Accepted features" value={asText(acceptedCount)} tone="good" sub="year-varying" />
        <MetricCard label="Frozen rejected" value={asText(frozen.length)} tone="bad" sub="snapshot columns" />
        <MetricCard label="Misaligned cols" value={asText(misaligned.length)} tone={misaligned.length ? 'warn' : 'good'} sub="2024 export" />
        <MetricCard label="Benchmark" value={bench.excess_outperform_targets_enabled ? 'Available' : 'Missing'} tone={bench.excess_outperform_targets_enabled ? 'good' : 'warn'} sub="targets" />
        <MetricCard label="Manual financials" value={d.manual_financials_present ? 'Present' : 'None'} tone={d.manual_financials_present ? 'good' : 'warn'} />
      </div>

      {/* Accepted vs Rejected two-column */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px,1fr))', gap: 16 }}>
        <EvidencePanel title="Accepted features" sub="Genuinely year-varying — safe for T→T+1 modeling" tone="good">
          {Object.entries(groups).map(([g, arr]) => (
            <div key={g}>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-3)', marginBottom: 5 }}>{g} ({(arr || []).length})</div>
              <RenderList items={arr} color="success" empty="none" />
            </div>
          ))}
        </EvidencePanel>

        <EvidencePanel title="Rejected frozen columns" sub="Same snapshot repeated across every period — no per-year signal" tone="bad">
          <RenderList items={frozen} color="danger" empty="none" />
          {misaligned.length > 0 && (
            <div>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--warning-light)', margin: '4px 0 5px' }}>Misaligned (2024 export)</div>
              <RenderList items={misaligned} color="warning" empty="none" />
            </div>
          )}
        </EvidencePanel>
      </div>

      {/* Corrected yearly ingestion status */}
      {cy.available && (
        <EvidencePanel title="Corrected yearly financials — verified per-year history" tone="good"
          sub={`${asText(cy.rows_written)} rows ingested · income & profitability now genuinely vary by year`}>
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--success-light)', marginBottom: 5 }}>Accepted (non-frozen) — {(cy.accepted_columns || []).length}</div>
            <RenderList items={cy.accepted_columns} color="success" empty="none" />
          </div>
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--danger-light)', margin: '4px 0 5px' }}>Valuation still frozen — rejected</div>
            <RenderList items={cy.frozen_valuation_columns} color="danger" empty="none" />
          </div>
          {(cy.misalignment_2024_columns || []).length > 0 && (
            <div>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--warning-light)', margin: '4px 0 5px' }}>2024 misalignment handled (cells rejected, not imputed)</div>
              <RenderList items={cy.misalignment_2024_columns} color="warning" empty="none" />
            </div>
          )}
        </EvidencePanel>
      )}

      {/* Evidence per source */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px,1fr))', gap: 16 }}>
        <EvidencePanel title="Yearly XLSX exports" tone="warn"
          footer="Valuation / profitability / income identical across all 6 years.">
          <Bullets tone="warn" size={12.5} items={[
            'P/E, P/B, EV/EBITDA, ROE, ROA, margins, revenue, net income, market cap repeat unchanged each year.',
            'Single point-in-time snapshot copied into every file — carries no T→T+1 historical signal.',
            '2024 file additionally has misaligned columns.',
          ]} />
        </EvidencePanel>
        <EvidencePanel title="Quarterly Fintables exports" tone="warn"
          footer="Same defect across all 8 quarterly periods.">
          <Bullets tone="warn" size={12.5} items={[
            'new_data_quarter Q1–Q4 (2020–2021) show the same frozen valuation/profitability values.',
            'Not usable as time-varying fundamentals despite being labelled per-quarter.',
            'Balance-sheet & growth fields remain the only genuinely varying inputs.',
          ]} />
        </EvidencePanel>
      </div>

      <WarningCallout title="Why frozen columns are rejected" tone="bad">
        Columns such as <b>P/E, ROE, revenue and market cap</b> are valuable in theory, but rejected because
        the current exports repeat the same snapshot across periods. The validator excludes any column whose
        value never changes per company — it cannot carry next-year predictive information.
      </WarningCallout>

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

      {/* Raw evidence */}
      <div>
        <CollapsibleJson label={evi?.available ? `Frozen-column evidence report — ${asText(evi.verdict)}` : 'Frozen-column evidence report (run make frozen-evidence)'}
          value={evi?.available ? evi.columns : { note: 'evidence report not generated yet' }} />
      </div>
    </div>
  )
}
