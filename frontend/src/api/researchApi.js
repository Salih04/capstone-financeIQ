import api from './client'

/* Centralized research-agent API layer. Every call returns
   { data, error } and never throws — pages stay crash-free. */

async function safeGet(path, params) {
  try {
    const res = await api.get(path, params ? { params } : undefined)
    return { data: res.data, error: null }
  } catch (e) {
    const d = e?.response?.data?.detail
    return { data: null, error: typeof d === 'string' ? d : (e?.message || 'request failed') }
  }
}
async function safePost(path, body) {
  try {
    const res = await api.post(path, body)
    return { data: res.data, error: null }
  } catch (e) {
    const d = e?.response?.data?.detail
    return { data: null, error: typeof d === 'string' ? d : (e?.message || 'request failed') }
  }
}

export const researchApi = {
  summary: () => safeGet('/research/summary'),
  diagnostics: () => safeGet('/research/model-diagnostics'),
  dataQuality: () => safeGet('/research/data-quality'),
  experiments: () => safeGet('/research/experiments'),
  significance: () => safeGet('/research/significance'),
  regimeContext: () => safeGet('/research/regime-context'),
  returnBasis: () => safeGet('/research/return-basis'),
  calibration: () => safeGet('/research/calibration'),
  autopsy: () => safeGet('/research/significance/autopsy'),
  courtroom: (ticker, year) => safePost('/research/courtroom', year ? { ticker, year: Number(year) } : { ticker }),
  benchmark: () => safeGet('/research/benchmark'),
  companies: () => safeGet('/research/companies'),
  frozenEvidence: () => safeGet('/research/frozen-evidence'),
  company: (ticker) => safeGet(`/research/company/${encodeURIComponent(ticker)}`),
  companyScore: (ticker) => safeGet(`/research/company/${encodeURIComponent(ticker)}/score`),
  skeptic: (ticker) => safeGet(`/research/skeptic/${encodeURIComponent(ticker)}`),
  ask: (question, ticker) => safePost('/research/ask', ticker ? { question, ticker } : { question }),
}

export default researchApi
