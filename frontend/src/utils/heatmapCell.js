// Display rules for one sector-heatmap cell. The API sends `value: null` when a
// cell has no finite observation; that must read as missing, never as 0.00.
// A real zero stays 0.00. Anything that is not a finite number is missing too.

export const MISSING_TEXT = '—'

export function heatCell(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return { missing: true, text: MISSING_TEXT }
  }
  const v = Math.max(-1, Math.min(1, value / 100))
  return {
    missing: false,
    text: (value === 0 ? 0 : value).toFixed(2),
    positive: v >= 0,
    opacity: 0.35 + Math.min(0.9, Math.abs(v)),
  }
}

const isCount = (n) => Number.isInteger(n) && n >= 0

// "observed of total" for a cell, or the missing marker if the counts are absent.
export function observationLabel(cell) {
  if (!cell || !isCount(cell.n_observed) || !isCount(cell.n_missing)) return MISSING_TEXT
  return `${cell.n_observed} of ${cell.n_observed + cell.n_missing}`
}
