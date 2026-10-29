import { test as base, expect } from '@playwright/test'

// Local browser fixtures only. No provider, production API, model or real data.
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url())
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort()
      if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/auth/')) {
        throw new Error(`Unmocked API request: ${url.pathname}`)
      }
      return route.continue()
    })
    await page.addInitScript(() => {
      const session = {
        access_token: 'synthetic-browser-token', token_type: 'bearer',
        expires_at: 4102444800, expires_in: 3600, refresh_token: 'synthetic-refresh',
        user: { id: 'synthetic-user', aud: 'authenticated', role: 'authenticated',
          email: 'synthetic@example.org', app_metadata: { provider: 'email', role: 'investor' },
          user_metadata: {}, created_at: '2021-01-01T00:00:00Z' },
      }
      // Supabase uses the first host label for its local storage key.
      localStorage.setItem('sb-127-auth-token', JSON.stringify(session))
    })
    await use(page)
  },
})
export { expect }
