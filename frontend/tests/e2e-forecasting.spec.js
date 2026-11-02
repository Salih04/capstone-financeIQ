import { test, expect } from './synthetic-session'

test('synthetic session -> current forecasting API flow -> ranked field', async ({ page }) => {
  const calls = []
  await page.route('**/api/forecasting/**', async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    calls.push({ path, body: request.postDataJSON() })
    let json
    if (path.endsWith('/options')) json = { trainable_years: [2020, 2021], all_years: [2021], inference_years: [], ticker_count: 1 }
    else if (path.endsWith('/inference')) json = { items: [] }
    else if (path.endsWith('/train')) json = { top_parameters: [{ name: 'Synthetic ROE', weight: 1, rank: 1 }] }
    else if (path.endsWith('/run')) json = { year: 2021, items: [{ ticker: 'SYN', score: 1, rank: 1, confidence: 'low' }] }
    else throw new Error(`Unexpected forecasting request: ${path}`)
    await route.fulfill({ json })
  })
  await page.goto('/forecasting')
  await expect(page.getByText('FINANCEIQ · FORECASTING SIGNAL TUNER', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'TRAIN PARAMETERS', exact: true }).click()
  await page.getByRole('button', { name: 'RUN FORECAST', exact: true }).click()
  await expect(page.locator('.ft-row-ticker')).toHaveText('SYN')
  expect(calls.find((c) => c.path.endsWith('/train')).body).toMatchObject({ train_year_from: 2020, train_year_to: 2021, target_mode: 'finalized_only' })
  expect(calls.find((c) => c.path.endsWith('/run')).body).toMatchObject({ year: 2021, trained_weights: { 'Synthetic ROE': 1 } })
})
