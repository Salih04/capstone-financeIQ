import { test, expect } from '@playwright/test'

const BASE = process.env.E2E_BASE_URL || 'http://localhost:3000'

test('login -> upload template trigger -> train -> predict -> detail navigation', async ({ page }) => {
  await page.goto(`${BASE}/login`)

  const email = `e2e_${Date.now()}@test.com`
  const password = 'Passw0rd!'

  await page.getByRole('button', { name: /kayıt ol/i }).click()
  await page.getByPlaceholder(/email/i).fill(email)
  await page.getByPlaceholder(/password/i).fill(password)
  await page.getByRole('button', { name: /hesap oluştur/i }).click()

  await page.waitForURL(/dashboard|forecasting|companies|compare|reports/)

  await page.goto(`${BASE}/forecasting`)

  await expect(page.getByText(/Success DNA Forecasting/i)).toBeVisible()

  await page.getByRole('button', { name: /Train Parameters/i }).click()
  await page.getByRole('button', { name: /Run Forecast/i }).click()

  const detailBtn = page.getByRole('button', { name: /Open Detail Charts/i })
  if (await detailBtn.count()) {
    await detailBtn.first().click()
    await expect(page).toHaveURL(/forecasting\/detail/)
  }
})
