import { test, expect } from '@playwright/test';

test.describe('Unauthenticated', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('redirects to login page', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('**/login');
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
  });

  test('login page loads without errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignore expected 401 from auth refresh attempt when not logged in
        if (text.includes('401')) return;
        errors.push(text);
      }
    });

    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
    await expect(page.getByLabel('Email address')).toBeVisible();
    await expect(page.getByLabel('Password', { exact: true })).toBeVisible();
    expect(errors).toHaveLength(0);
  });
});

test.describe('Authenticated', () => {
  test('dashboard loads with expected elements', async ({ page }) => {
    await page.goto('/dashboard');
    // Wait for page to fully load - may show empty state or accounts
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Personal Finance', exact: true })).toBeVisible();
    // User menu button contains user initials from display_name
    await expect(page.locator('[data-slot="button"][aria-haspopup="menu"]')).toBeVisible();
  });
});
