import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('app loads without errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await expect(page).toHaveTitle(/Personal Finance/);
    await expect(page.getByRole('heading', { name: 'Personal Finance' })).toBeVisible();
    expect(errors).toHaveLength(0);
  });

  test('app renders key UI elements', async ({ page }) => {
    await page.goto('/');

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
