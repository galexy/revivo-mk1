/**
 * E2E tests for account CRUD operations.
 * Tests full flow: frontend wizard → API → database → cache invalidation → UI update.
 */
import { test, expect } from '@playwright/test';

/**
 * Helper to open the account wizard.
 * Handles both empty state and sidebar "Add" button scenarios.
 */
async function openAccountWizard(page: any) {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Wait for dashboard to load (confirms auth worked)
  await expect(page.getByRole('heading', { name: 'Personal Finance', exact: true })).toBeVisible({ timeout: 10000 });

  // Try empty state button first (visible when no accounts exist)
  const emptyStateButton = page.getByRole('button', { name: /add your first account/i });
  const isEmptyState = await emptyStateButton.isVisible({ timeout: 1000 }).catch(() => false);

  if (isEmptyState) {
    await emptyStateButton.click();
  } else {
    // Otherwise use sidebar Add button
    await page.getByTitle('Add Account').click();
  }

  // Wait for wizard dialog to open
  await expect(page.getByRole('dialog')).toBeVisible();
}

test.describe('Account CRUD', () => {
  test('creates a checking account via wizard', async ({ page }) => {
    await openAccountWizard(page);

    // Step 1: Select Checking account type (it's a radio button, not a regular button)
    await page.getByLabel(/checking/i).click({ force: true });

    // Wait for Next button to be enabled after selection
    const nextButton = page.getByRole('button', { name: /next/i });
    await expect(nextButton).toBeEnabled();
    await nextButton.click();

    // Step 2: Enter account name (unique per test run)
    const accountName = `Test Checking ${Date.now()}`;
    await expect(page.getByRole('dialog').getByText('Account Details').first()).toBeVisible();
    await page.getByLabel('Account Name').fill(accountName);
    await page.getByRole('button', { name: /next/i }).click();

    // Step 3: Enter opening balance
    await expect(page.getByRole('dialog').getByText('Opening Balance').first()).toBeVisible();
    await page.getByLabel(/opening balance/i).fill('1000');
    await page.getByRole('button', { name: /next/i }).click();

    // Step 4: Review and create
    await expect(page.getByRole('dialog').getByText('Review & Confirm').first()).toBeVisible();
    await expect(page.getByRole('dialog').getByText(accountName)).toBeVisible();
    await expect(page.getByRole('dialog').getByText('$1,000.00')).toBeVisible();
    await page.getByRole('button', { name: /create account/i }).click();

    // Wait for dialog to close and account to appear in sidebar
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });

    // Verify account appears in sidebar
    await expect(page.getByText(accountName)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('$1,000.00')).toBeVisible();
  });

  test('edits an account via wizard', async ({ page }) => {
    // Setup: Create account via wizard first
    const initialName = `Test Edit ${Date.now()}`;

    await openAccountWizard(page);

    // Create savings account
    await page.getByLabel(/savings/i).click({ force: true });
    await expect(page.getByRole('button', { name: /next/i })).toBeEnabled();
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByLabel('Account Name').fill(initialName);
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByLabel(/opening balance/i).fill('500');
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /create account/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
    await expect(page.getByText(initialName)).toBeVisible({ timeout: 10000 });

    // Now edit the account
    // Find the account list item button and hover to reveal menu
    const accountButton = page.locator('button').filter({ hasText: initialName }).first();
    await accountButton.hover();

    // Click the dropdown menu button (three dots) - it's near the account
    // Look for any button with aria-haspopup=menu in the vicinity
    await page.locator('button[aria-haspopup="menu"]').first().click();

    // Click Edit option from dropdown
    await page.getByRole('menuitem', { name: /edit/i }).click();

    // Wait for wizard to open in edit mode
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('dialog').getByText('Edit Account')).toBeVisible();

    // Change name
    const updatedName = `Updated ${initialName}`;
    const nameInput = page.getByLabel('Account Name');
    await nameInput.click();
    await nameInput.clear();
    await nameInput.fill(updatedName);
    await page.getByRole('button', { name: /next/i }).click();

    // Skip opening balance step
    await page.getByRole('button', { name: /next/i }).click();

    // Review and save
    await expect(page.getByRole('dialog').getByText(updatedName)).toBeVisible();
    await page.getByRole('button', { name: /save changes/i }).click();

    // Wait for dialog to close and verify updated name in sidebar
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
    await expect(page.getByText(updatedName)).toBeVisible({ timeout: 10000 });
  });

  test('deletes an account via type-to-confirm', async ({ page }) => {
    // Setup: Create account via wizard first
    const accountName = `Delete Me ${Date.now()}`;

    await openAccountWizard(page);

    // Create credit card account
    await page.getByLabel(/credit card/i).click({ force: true });
    await expect(page.getByRole('button', { name: /next/i })).toBeEnabled();
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByLabel('Account Name').fill(accountName);
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByLabel(/credit limit/i).fill('5000');
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByLabel(/opening balance/i).fill('250');
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /create account/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
    await expect(page.getByText(accountName)).toBeVisible({ timeout: 10000 });

    // Now delete the account
    const accountButton = page.locator('button').filter({ hasText: accountName }).first();
    await accountButton.hover();

    // Click the dropdown menu button
    await page.locator('button[aria-haspopup="menu"]').first().click();

    // Click Delete option
    await page.getByRole('menuitem', { name: /delete/i }).click();

    // Wait for delete confirmation dialog
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('dialog').getByText('Delete Account')).toBeVisible();

    // Type account name to confirm (find the input field)
    const confirmInput = page.getByRole('dialog').getByRole('textbox');
    await confirmInput.fill(accountName);

    // Click Delete button
    await page.getByRole('dialog').getByRole('button', { name: /delete account/i }).click();

    // Wait for dialog to close and verify account removed from sidebar
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });

    // Account should no longer be visible
    await expect(page.getByText(accountName)).not.toBeVisible({ timeout: 10000 });
  });
});
