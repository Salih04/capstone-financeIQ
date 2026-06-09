import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BrainCircuit, Upload, Play, ListOrdered, Info, ShieldCheck, Sparkles } from 'lucide-react'
import api from '../api/client'
import { Card, EmptyState } from '../components/ui'

const PRESET_FILES = [
  '2020stocks.xlsx',
  '2021stocks.xlsx',
  '2022stocks.xlsx',
  '2023stocks.xlsx',
  '2024stocks.xlsx',
  '2025stocks.xlsx',
]

const inputS = {
  width: '100%',
  boxSizing: 'border-box',
  background: 'var(--surface-1)',
  border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--text-1)',
  padding: '9px 12px',
  fontSize: 13,
  outline: 'none',
}

export default function ForecastingPage() {
  const navigate = useNavigate()
  const [userType, setUserType] = useState('individual')
  const [riskLevel, setRiskLevel] = useState('medium')
  const [investmentScope, setInvestmentScope] = useState('')
  const [portfolioInput, setPortfolioInput] = useState('')
  const [portfolioResult, setPortfolioResult] = useState(null)
  const [uploaded, setUploaded] = useState([])
  const [filters, setFilters] = useState({ years: [], sectors: [] })
  const [year, setYear] = useState('')
  const [sector, setSector] = useState('')
  const [training, setTraining] = useState(false)
  const [running, setRunning] = useState(false)
  const [cvLoading, setCvLoading] = useState(false)
  const [modelResult, setModelResult] = useState(null)
  const [stocksResult, setStocksResult] = useState(null)
  const [selectedStock, setSelectedStock] = useState(null)
  const [detail, setDetail] = useState(null)
  const [msg, setMsg] = useState('')
  const [modelType, setModelType] = useState('scoring')
  const [evaluation, setEvaluation] = useState(null)
  const [history, setHistory] = useState([])
  const [catalog, setCatalog] = useState([])
  const [fundamentalsFile, setFundamentalsFile] = useState(null)

  const loadFilters = async () => {
    try {
      const { data } = await api.get('/forecasting/filters')
      setFilters(data)
      if (!year && data.years?.length) setYear(String(data.years[data.years.length - 1]))
      if (!sector && data.sectors?.length) setSector(data.sectors[0])
    } catch {
      setFilters({ years: [], sectors: [] })
    }
  }

  useEffect(() => {
    loadFilters()
    api.get('/predict/history').then(({ data }) => setHistory(data.items || [])).catch(() => setHistory([]))
    api.get('/parameters/catalog').then(({ data }) => setCatalog(data.items || [])).catch(() => setCatalog([]))
  }, [])

  const uploadPreset = async (fileName) => {
    setMsg('')
    try {
      const { data } = await api.post('/upload-data', { file_name: fileName })
      setUploaded((prev) => [data, ...prev])
      await loadFilters()
      setMsg(`${fileName} imported (${data.imported_rows} rows).`)
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Import failed.')
    }
  }

  const uploadFundamentals = async () => {
    if (!fundamentalsFile) {
      setMsg('Please select quarterly fundamentals CSV first.')
      return
    }
    const form = new FormData()
    form.append('file', fundamentalsFile)
    try {
      const { data } = await api.post('/fundamentals/upload-csv', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      // Refetch filters: uploaded fundamentals carry sector + year, so Year/Sector
      // dropdowns should now populate and Train Parameters become usable.
      await loadFilters()
      setMsg(`Corrected financial history loaded (created=${data.created}, updated=${data.updated}, skipped=${data.skipped}). Year/Sector refreshed.`)
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Fundamentals upload failed.')
    }
  }

  const trainModel = async () => {
    if (!year || !sector) {
      setMsg('Select year and sector first.')
      return
    }
    setTraining(true)
    setMsg('')
    try {
      const { data } = await api.post('/train-model', {
        year: parseInt(year, 10),
        sector,
        top_n_parameters: 8,
      })
      setModelResult(data)
      setMsg(`Model trained for ${sector} (${year}).`)
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Training failed.')
    } finally {
      setTraining(false)
    }
  }

  const runForecast = async () => {
    if (!year || !sector) {
      setMsg('Select year and sector first.')
      return
    }
    setRunning(true)
    setMsg('')
    try {
      const { data } = await api.post('/predict', {
        year: parseInt(year, 10),
        sector,
        user_type: userType,
        risk_level: riskLevel,
        investment_scope: investmentScope ? parseFloat(investmentScope) : null,
        model_type: modelType,
      })
      setStocksResult(data)
      setSelectedStock(null)
      setDetail(null)
      setMsg(`Forecast run completed. ${data.items.length} stocks ranked.`)
      api.get('/predict/history').then(({ data: h }) => setHistory(h.items || [])).catch(() => {})
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Forecast failed.')
    } finally {
      setRunning(false)
    }
  }

  const runEvaluation = async () => {
    if (!sector) {
      setMsg('Select sector for evaluation.')
      return
    }
    if (cvLoading) return
    setCvLoading(true)
    try {
      const { data } = await api.post('/predict/evaluate', {
        sector,
        model_type: modelType,
        window_size: 2,
      })
      setEvaluation(data)
      setMsg('Time-CV evaluation completed.')
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Evaluation failed. You can try again.')
    } finally {
      setCvLoading(false)
    }
  }

  const analyzePortfolio = async () => {
    if (!year || !sector) {
      setMsg('Select year and sector first.')
      return
    }
    const stock_codes = portfolioInput
      .split(/[\s,;]+/)
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean)
    if (stock_codes.length === 0) {
      setMsg('Enter at least one stock code for portfolio analysis.')
      return
    }
    try {
      const { data } = await api.post('/get-portfolio-analysis', {
        year: parseInt(year, 10),
        sector,
        stock_codes,
      })
      setPortfolioResult(data)
      setMsg('Portfolio analysis completed.')
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Portfolio analysis failed.')
    }
  }

  const openStock = async (stockCode) => {
    if (!stocksResult?.run_id) return
    setSelectedStock(stockCode)
    try {
      const { data } = await api.get('/get-stock-detail', {
        params: { run_id: stocksResult.run_id, stock_code: stockCode },
      })
      setDetail(data)
    } catch {
      setDetail(null)
    }
  }

  const canRun = Boolean(year && sector)

  const topParams = useMemo(() => modelResult?.top_parameters || [], [modelResult])

  return (
    <div style={{ maxWidth: 1150, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <section style={forecastHero}>
        <div style={heroKicker}><Sparkles size={15} /> Experimental Forecasting</div>
        <h1 style={heroTitle}>Legacy forecasting tools, clearly marked as experimental.</h1>
        <p style={heroSub}>
          Import winner files, train parameter profiles, and run ranking experiments. This page supports exploration only and must not be read as production prediction or investment advice.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 }}>
          <span style={heroBadge}><BrainCircuit size={13} /> Experimental</span>
          <span style={heroBadge}><ShieldCheck size={13} /> Diagnostic output</span>
        </div>
      </section>

      {msg && (
        <div style={{ marginBottom: 14, fontSize: 13, color: 'var(--text-2)', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '9px 12px' }}>
          {msg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: 16, marginBottom: 16 }}>
        <Card style={{ padding: '1rem' }}>
           <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 10 }}>Step 1: Import Winner Files</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {PRESET_FILES.map((f) => (
              <button
                key={f}
                onClick={() => uploadPreset(f)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  border: '1px solid var(--border-strong)',
                  background: 'var(--surface-1)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-1)',
                  fontSize: 12,
                  padding: '8px 10px',
                  cursor: 'pointer',
                }}
              >
                <Upload size={13} />
                {f}
              </button>
            ))}
          </div>
          {uploaded.length > 0 && (
            <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-3)' }}>
              Last import: {uploaded[0].file_name} ({uploaded[0].imported_rows} rows)
            </div>
          )}

          <div style={{ marginTop: 14, borderTop: '1px solid var(--border)', paddingTop: 10 }}>
           <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 8 }}>Upload Quarterly Fundamentals (Exact Ratios, CSV)</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8 }}>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFundamentalsFile(e.target.files?.[0] || null)}
                style={{ ...inputS, padding: '7px 10px' }}
              />
              <button
                onClick={uploadFundamentals}
                style={{
                  border: '1px solid var(--border-strong)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--surface-1)',
                  color: 'var(--text-1)',
                  fontSize: 12,
                  padding: '8px 12px',
                  cursor: 'pointer',
                }}
              >
                Upload CSV
              </button>
            </div>
          </div>
        </Card>

        <Card style={{ padding: '1rem' }}>
           <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 10 }}>Step 2: User Setup and Scope</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
            <select value={userType} onChange={(e) => setUserType(e.target.value)} style={inputS}>
              <option value="individual">Individual</option>
              <option value="advanced">Advanced</option>
              <option value="corporate">Corporate</option>
            </select>
            <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)} style={inputS}>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 8 }}>
            <select value={year} onChange={(e) => setYear(e.target.value)} style={inputS}>
              <option value="">Year</option>
              {filters.years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
            <select value={sector} onChange={(e) => setSector(e.target.value)} style={inputS}>
              <option value="">Sector</option>
              {filters.sectors.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          {(filters.years.length === 0 || filters.sectors.length === 0) && (
            <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--text-3)', lineHeight: 1.5 }}>
              Year & Sector populate after importing a Winner file (Step 1) or uploading quarterly
              fundamentals (Step 2). After upload they refresh automatically.
            </div>
          )}
          <select value={modelType} onChange={(e) => setModelType(e.target.value)} style={{ ...inputS, marginTop: 8 }}>
            <option value="scoring">Scoring (Primary)</option>
            <option value="dbscan">Cluster Profile</option>
            <option value="gmm">Mixture Profile</option>
            <option value="xgboost">Tree Ensemble</option>
            <option value="prophet">Trend Projection</option>
            <option value="arima">Momentum Projection</option>
          </select>
          <input
            value={investmentScope}
            onChange={(e) => setInvestmentScope(e.target.value)}
            placeholder="Investment scope (optional amount)"
            style={{ ...inputS, marginTop: 8 }}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <button
              onClick={trainModel}
              disabled={training}
              title={canRun ? 'Train solid-parameter model' : 'Select year and sector first'}
              style={{
                border: 'none',
                borderRadius: 'var(--radius-md)',
                background: 'var(--primary)',
                color: '#fff',
                fontSize: 12,
                padding: '8px 12px',
                cursor: training ? 'wait' : 'pointer',
                opacity: training ? 0.7 : canRun ? 1 : 0.75,
              }}
            >
              {training ? 'Training...' : 'Train Parameters'}
            </button>
            <button
              onClick={runForecast}
              disabled={running}
              title={canRun ? 'Run forecast' : 'Select year and sector first'}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                background: 'var(--surface-1)',
                color: 'var(--text-1)',
                fontSize: 12,
                padding: '8px 12px',
                cursor: running ? 'wait' : 'pointer',
                opacity: running ? 0.7 : canRun ? 1 : 0.85,
              }}
            >
              <Play size={13} />
              {running ? 'Running...' : 'Run Forecast'}
            </button>
            <button
              onClick={runEvaluation}
              disabled={cvLoading}
              style={{
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                background: 'var(--surface-1)',
                color: 'var(--text-1)',
                fontSize: 12,
                padding: '8px 12px',
                cursor: cvLoading ? 'wait' : 'pointer',
              }}
            >
              {cvLoading ? 'Running CV…' : 'Run Time CV'}
            </button>
          </div>
        </Card>
      </div>

      {evaluation && (
        <Card style={{ padding: '1rem', marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 }}>
            Rolling Window Evaluation
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 6 }}>
            Mean Rank Stability: {evaluation.mean_rank_stability != null ? evaluation.mean_rank_stability.toFixed(4) : 'n/a'}
            {' | '}
            Mean Overlap@10: {evaluation.mean_overlap_at_k != null ? evaluation.mean_overlap_at_k.toFixed(4) : 'n/a'}
          </div>
          {(evaluation.folds || []).map((f) => (
            <div key={f.fold_index} style={{ borderTop: '1px solid var(--border)', padding: '8px 0', fontSize: 12, color: 'var(--text-2)' }}>
              Fold {f.fold_index}: Train {f.train_year_start}-{f.train_year_end}, Test {f.test_year}, Stability {f.rank_stability != null ? f.rank_stability.toFixed(4) : 'n/a'}, Overlap@10 {f.overlap_at_k != null ? f.overlap_at_k.toFixed(4) : 'n/a'}
            </div>
          ))}
        </Card>
      )}

      {userType === 'corporate' && (
        <Card style={{ padding: '1rem', marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 }}>
            Corporate Portfolio Mode
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8 }}>
            <input
              value={portfolioInput}
              onChange={(e) => setPortfolioInput(e.target.value)}
              placeholder="Enter stock codes (comma separated), e.g. ASELS, TUPRS, THYAO"
              style={inputS}
            />
            <button
              onClick={analyzePortfolio}
              style={{
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                background: 'var(--surface-1)',
                color: 'var(--text-1)',
                fontSize: 12,
                padding: '8px 12px',
                cursor: 'pointer',
              }}
            >
              Analyze Portfolio
            </button>
          </div>

          {portfolioResult && (
            <div style={{ marginTop: 10, fontSize: 12 }}>
              <div style={{ fontWeight: 700, color: 'var(--text-2)', marginBottom: 6 }}>Suggestions</div>
              {portfolioResult.optimization_actions?.map((a, idx) => (
                <div key={idx} style={{ borderTop: '1px solid var(--border)', padding: '7px 0', color: 'var(--text-2)' }}>
                  {a}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: 16 }}>
        <Card style={{ padding: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <ListOrdered size={15} style={{ color: 'var(--primary)' }} />
            <span style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6 }}>Ranked Stocks</span>
          </div>
          {!stocksResult?.items?.length ? (
            <EmptyState title="No forecast yet" description="Run forecast to generate stock rankings." />
          ) : (
            <div style={{ maxHeight: 500, overflowY: 'auto' }}>
              {stocksResult.items.map((item) => (
                <button
                  key={item.stock_code}
                  onClick={() => openStock(item.stock_code)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    display: 'grid',
                    gridTemplateColumns: '52px 1fr 80px 90px',
                    gap: 8,
                    alignItems: 'center',
                    border: 'none',
                    borderTop: '1px solid var(--border)',
                    background: selectedStock === item.stock_code ? 'var(--surface-1)' : 'transparent',
                    color: 'var(--text-1)',
                    padding: '10px 6px',
                    cursor: 'pointer',
                  }}
                >
                  <span style={{ fontSize: 12, color: 'var(--text-3)' }}>#{item.rank}</span>
                  <span style={{ fontWeight: 700 }}>{item.stock_code}</span>
                  <span style={{ fontWeight: 700, color: 'var(--primary)' }}>{item.score.toFixed(2)}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-3)' }}>C {Math.round(item.confidence * 100)}%</span>
                </button>
              ))}
            </div>
          )}

          {selectedStock && year && sector && (
            <div style={{ marginTop: 10 }}>
              <button
                onClick={() => navigate(`/forecasting/detail?stock=${encodeURIComponent(selectedStock)}&sector=${encodeURIComponent(sector)}&year=${encodeURIComponent(year)}`)}
                style={{
                  border: '1px solid var(--border-strong)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--surface-1)',
                  color: 'var(--text-1)',
                  fontSize: 12,
                  padding: '8px 12px',
                  cursor: 'pointer',
                }}
              >
                Open Detail Charts
              </button>
            </div>
          )}
        </Card>

        <Card style={{ padding: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <Info size={15} style={{ color: 'var(--primary)' }} />
            <span style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6 }}>Explainability</span>
          </div>

          {topParams.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-2)', marginBottom: 8 }}>Top Solid Parameters</div>
              {topParams.slice(0, 6).map((p) => (
                <div key={p.parameter_name} style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border)', padding: '7px 0', fontSize: 12 }}>
                  <span style={{ color: 'var(--text-2)' }}>{p.parameter_name}</span>
                  <span style={{ color: 'var(--primary)', fontWeight: 700 }}>{p.score.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}

          {detail ? (
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-2)', marginBottom: 8 }}>
                Why {detail.stock_code}?
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 8 }}>
                Score {detail.score.toFixed(2)} | Rank #{detail.rank} | Confidence {Math.round(detail.confidence * 100)}%
              </div>
              {detail.top_contributors?.map((c) => (
                <div key={c.parameter_name} style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border)', padding: '7px 0', fontSize: 12 }}>
                  <span>{c.parameter_name}</span>
                  <span style={{ fontWeight: 700 }}>{c.contribution.toFixed(4)}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Select a stock" description="Click any ranked stock to inspect top contributing parameters." />
          )}
        </Card>
      </div>

      <Card style={{ padding: '1rem', marginTop: 16 }}>
        <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 }}>
          Predict History
        </div>
        {history.length === 0 ? (
          <EmptyState title="No history yet" description="Run predictions to populate history." />
        ) : (
          history.slice(0, 20).map((h) => (
            <div key={h.run_id} style={{ borderTop: '1px solid var(--border)', padding: '8px 0', fontSize: 12, color: 'var(--text-2)' }}>
              #{h.run_id} | {h.sector} | {h.year} | {new Date(h.created_at).toLocaleString('en-US')}
            </div>
          ))
        )}
      </Card>

      <Card style={{ padding: '1rem', marginTop: 16 }}>
        <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 }}>
          Parameter Catalog (Requested)
        </div>
        {catalog.length === 0 ? (
          <EmptyState title="No parameter catalog" description="Catalog endpoint has no data." />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>Category</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>Ratio</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>Formula</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>Purpose</th>
                </tr>
              </thead>
              <tbody>
                {catalog.map((c, i) => (
                  <tr key={`${c.ratio}-${i}`}>
                    <td style={{ borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>{c.category}</td>
                    <td style={{ borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>{c.ratio}</td>
                    <td style={{ borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>{c.formula}</td>
                    <td style={{ borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>{c.purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

const forecastHero = { border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))', padding: 24, marginBottom: 18 }
const heroKicker = { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 }
const heroTitle = { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2rem, 5vw, 3.25rem)', lineHeight: 1, fontWeight: 900, maxWidth: 860 }
const heroSub = { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 780 }
const heroBadge = { display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-strong)', borderRadius: 999, padding: '6px 10px', color: 'var(--text-2)', fontSize: 12, fontWeight: 800 }
