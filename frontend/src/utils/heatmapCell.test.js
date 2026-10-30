// Sector heatmap display: a missing cell renders as missing, never as 0.00,
// and a real zero still renders as 0.00. Synthetic values only.
// Node's built-in runner, no extra dependency: npm run test:unit
import test from 'node:test'
import assert from 'node:assert/strict'
import { heatCell, observationLabel } from './heatmapCell.js'

test('null, absent and non-finite values render as missing, not 0.00', () => {
  for (const value of [null, undefined, NaN, Infinity, -Infinity, '0', '1.5', {}]) {
    const cell = heatCell(value)
    assert.equal(cell.missing, true, String(value))
    assert.equal(cell.text, '—', String(value))
    assert.notEqual(cell.text, '0.00')
  }
})

test('a real zero renders as 0.00 and is not missing', () => {
  for (const value of [0, -0]) {
    const cell = heatCell(value)
    assert.equal(cell.missing, false)
    assert.equal(cell.text, '0.00')
    assert.equal(cell.positive, true)
  }
})

test('finite values keep their sign, text and bounded opacity', () => {
  assert.deepEqual(heatCell(12.5), { missing: false, text: '12.50', positive: true, opacity: 0.475 })
  assert.deepEqual(heatCell(-150), { missing: false, text: '-150.00', positive: false, opacity: 1.25 })
})

test('observation counts show how many values a cell averaged', () => {
  assert.equal(observationLabel({ n_observed: 2, n_missing: 1 }), '2 of 3')
  assert.equal(observationLabel({ n_observed: 0, n_missing: 4 }), '0 of 4')
  for (const cell of [{}, { n_observed: 2 }, { n_observed: -1, n_missing: 1 }, { n_observed: 1.5, n_missing: 0 }, null]) {
    assert.equal(observationLabel(cell), '—')
  }
})
