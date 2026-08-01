import { test, expect } from '@playwright/test'

const LOCAL_SESSION = {
  access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRlbW8iLCJyb2xlIjoiYW5vbiIsImlhdCI6MTcwMDAwMDAwMCwiZXhwIjoxOTAwMDAwMDAwMH0.signature',
  token_type: 'bearer',
  expires_in: 3600,
  expires_at: 1900000000,
  refresh_token: 'local-courtroom-test-refresh-token',
  user: {
    id: 'local-courtroom-test-user',
    aud: 'authenticated',
    role: 'authenticated',
    email: 'courtroom-test@example.com',
    app_metadata: { provider: 'email', providers: ['email'] },
    user_metadata: {},
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
}

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
  await page.addInitScript((session) => {
    localStorage.setItem('sb-demo-auth-token', JSON.stringify(session))
  }, LOCAL_SESSION)
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
