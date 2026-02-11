import { test, expect } from '@playwright/test';

test.describe('Unauthenticated', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('redirects to login page', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('**/login');
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
  });

  test('login page loads without errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    expect(errors).toHaveLength(0);
  });
});

test.describe('Authenticated', () => {
  test('dashboard loads after login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByText('Personal Finance')).toBeVisible();
  });

  test('dashboard has user menu', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('button')).toBeVisible();
  });

  test('dashboard renders key UI elements', async ({ page }) => {
    await page.goto('/dashboard');

    // Check sidebar with accounts
    await expect(page.getByRole('heading', { name: 'Accounts' })).toBeVisible();

    // Check account cards with balances
    await expect(page.getByText('$1,234.56')).toBeVisible();
    await expect(page.getByText('$15,678.90')).toBeVisible();
    await expect(page.getByText('-$542.30')).toBeVisible();

    // Check Quick Add Transaction form
    await expect(page.getByText('Quick Add Transaction')).toBeVisible();
    await expect(page.getByPlaceholder('Enter payee name')).toBeVisible();

    // Check theme toggle button
    await expect(page.getByRole('button', { name: /Mode/ })).toBeVisible();
  });
});
