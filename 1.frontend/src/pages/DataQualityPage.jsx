import { useEffect, useState } from 'react'
import { Database } from 'lucide-react'
import { Card, SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, RenderList, WarningCallout, JsonBlock, asText } from '../utils/safeRender'

export default function DataQualityPage() {
  const [dq, setDq] = useState(null)
  const [summary, setSummary] = useState(null)
  const [evi, setEvi] = useState(null)
  const [showEvi, setShowEvi] = useState(false)

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader title="Data Quality & Integrity" sub="Why columns are accepted or rejected — capstone evidence" icon={Database} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px,1fr))', gap: 12 }}>
        <MetricCard label="Accepted features" value={asText(ctx.feature_count)} tone="good" />
        <MetricCard label="Frozen rejected" value={asText(frozen.length)} tone="bad" />
        <MetricCard label="Misaligned cols" value={asText(misaligned.length)} tone={misaligned.length ? 'warn' : 'good'} />
        <MetricCard label="Benchmark" value={bench.excess_outperform_targets_enabled ? 'available' : 'missing'} tone={bench.excess_outperform_targets_enabled ? 'good' : 'warn'} />
        <MetricCard label="Manual financials" value={d.manual_financials_present ? 'present' : 'none'} tone={d.manual_financials_present ? 'good' : 'warn'} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px,1fr))', gap: 16 }}>
        <Card>
          <SectionHeader title="Accepted feature groups" sub="genuinely year-varying" />
          {Object.entries(groups).map(([g, arr]) => (
            <div key={g} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>{g} ({(arr || []).length})</div>
              <RenderList items={arr} empty="none" />
            </div>
          ))}
        </Card>
        <Card>
          <SectionHeader title="Rejected frozen columns" sub="repeated snapshot — no per-year signal" />
          <RenderList items={frozen} color="danger" empty="none" />
          {misaligned.length > 0 && (
            <>
              <div style={{ fontSize: 12, fontWeight: 700, margin: '10px 0 4px' }}>Misaligned (2024)</div>
              <JsonBlock value={misaligned} maxHeight={140} />
            </>
          )}
        </Card>
      </div>

      <WarningCallout title="Why frozen columns are rejected" tone="bad">
        For each ticker, valuation/profitability/income values (P/E, P/B, EV/EBITDA, ROE, ROA, margins,
        revenue, net income, market cap) are <b>identical across every year</b> — a single point-in-time
        snapshot repeated into each file. They carry no T→T+1 historical signal, so the validator excludes
        them. Quarterly Fintables exports show the <b>same defect</b> across all 8 periods.
      </WarningCallout>

      <Card>
        <SectionHeader title="Leakage controls" />
        <p style={{ fontSize: 13, color: 'var(--text-2)' }}>{asText(d.leakage_controls)}</p>
        <p style={{ fontSize: 12, color: 'var(--text-3)' }}>
          Leakage = using information not available before the target year. <code>next_year_*</code>,
          <code> same_year_return_pct</code>, and <code>target_year</code> can never be features.
        </p>
      </Card>

      <Card>
        <SectionHeader title="Frozen-column evidence report"
          actions={<button onClick={() => setShowEvi(s => !s)} style={btn}>{showEvi ? 'hide' : 'show JSON'}</button>} />
        <p style={{ fontSize: 13, color: 'var(--text-2)' }}>
          {evi?.available ? asText(evi.verdict) : 'Evidence report not generated yet — run `make frozen-evidence`.'}
        </p>
        {showEvi && evi?.available && <JsonBlock value={evi.columns} />}
      </Card>

      <WarningCallout title="What data is still needed">
        Real <b>per-year</b> income statement, profitability and year-end valuation (P/E, P/B, EV/EBITDA) per
        company. Provide via <code>data/trusted_raw/financials/</code> and re-run the pipeline; the validator
        will show those columns becoming non-frozen.
      </WarningCallout>
    </div>
  )
}

const btn = { background: 'var(--surface-1)', color: 'var(--text-2)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '4px 10px', fontSize: 12, cursor: 'pointer' }
