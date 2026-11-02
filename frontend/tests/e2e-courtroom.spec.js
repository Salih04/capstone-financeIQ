import { test, expect } from './synthetic-session'

async function openEvidenceDocket(page) {
  await page.goto('/courtroom')
  await page.getByLabel('TICKER', { exact: true }).fill('ASELS')
  await page.getByLabel('CONTEXT YEAR · OPTIONAL', { exact: true }).fill('2024')
  await page.getByRole('button', { name: 'OPEN EVIDENCE DOCKET', exact: true }).click()
  await expect(page.getByText('DETERMINISTIC · ASELS · 2024')).toBeVisible()
}

async function assertSequentialPanels(page) {
  const layout = await page.evaluate(() => Array.from(document.querySelectorAll('.cq-persona')).map((panel) => {
    const rect = panel.getBoundingClientRect()
    return {
      label: panel.querySelector('h2')?.textContent,
      top: rect.top,
      bottom: rect.bottom,
      position: getComputedStyle(panel).position,
    }
  }))

  expect(layout.map(({ label }) => label)).toEqual(['Bull', 'Bear', 'Skeptic', 'Risk'])
  expect(layout[2].top).toBeGreaterThanOrEqual(Math.max(layout[0].bottom, layout[1].bottom) - 1)
  expect(layout[3].top).toBeGreaterThanOrEqual(Math.max(layout[0].bottom, layout[1].bottom, layout[2].bottom) - 1)
  expect(layout[3].position).not.toBe('sticky')
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/research/courtroom', async (route) => {
    const { ticker, year } = route.request().postDataJSON()
    await route.fulfill({ json: {
      status: 'complete', ticker, year: year || 2021, evidence_budget_per_persona: 1,
      personas: ['bull', 'bear', 'skeptic', 'risk'].map((id) => ({
        persona_id: id, name: id[0].toUpperCase() + id.slice(1), lens: 'Synthetic layout fixture',
        items: [{ statement: 'Synthetic evidence for browser layout only.', limitation: 'No research evidence.',
          citation: { field: 'synthetic', value: null, source_file: 'synthetic-fixture' } }],
      })),
    } })
  })
})

test('Research Courtroom keeps the Risk evidence lens after earlier lenses on desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 })
  await openEvidenceDocket(page)
  await assertSequentialPanels(page)

  await page.getByLabel('CONTEXT YEAR · OPTIONAL', { exact: true }).fill('')
  await page.getByRole('button', { name: 'OPEN EVIDENCE DOCKET', exact: true }).click()
  await expect(page.locator('.cq-loaded')).toContainText('DETERMINISTIC · ASELS')
  await assertSequentialPanels(page)
})

test('Research Courtroom keeps all evidence lenses readable on narrow layouts', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await openEvidenceDocket(page)
  await assertSequentialPanels(page)
})
