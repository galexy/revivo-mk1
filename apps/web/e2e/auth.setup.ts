import { test as setup, expect } from '@playwright/test';

const TEST_USER = {
  email: 'e2e-test@example.com',
  password: 'TestPass123!',
  displayName: 'E2E Test User',
};

const API_BASE = 'http://localhost:8000';
const MAILPIT_API = 'http://mailpit:8025/api/v1';

setup('authenticate', async ({ page }) => {
  // Step 1: Try to log in first (user may already exist and be verified)
  await page.goto('/login');
  await page.getByLabel('Email').fill(TEST_USER.email);
  await page.getByLabel('Password').fill(TEST_USER.password);
  await page.getByRole('button', { name: /sign in/i }).click();

  // Wait briefly for response
  const loginResponse = await Promise.race([
    page.waitForURL('**/dashboard', { timeout: 5000 }).then(() => 'success'),
    page.waitForTimeout(5000).then(() => 'timeout'),
  ]);

  if (loginResponse === 'success') {
    // User already exists and is verified — save state and done
    await page.context().storageState({ path: 'apps/web/e2e/.auth/user.json' });
    return;
  }

  // Step 2: Register via API (POST /auth/register)
  await page.request.post(`${API_BASE}/auth/register`, {
    data: {
      email: TEST_USER.email,
      password: TEST_USER.password,
      display_name: TEST_USER.displayName,
    },
  });

  // Step 3: Get verification token from Mailpit
  await page.waitForTimeout(1000);

  const messagesResponse = await page.request.get(`${MAILPIT_API}/messages`);
  const messagesData = await messagesResponse.json();

  const verificationEmail = messagesData.messages?.find(
    (msg: { To: Array<{ Address: string }>; Subject: string }) =>
      msg.To?.some((to: { Address: string }) => to.Address === TEST_USER.email) &&
      msg.Subject?.includes('erif')
  );

  if (!verificationEmail) {
    throw new Error('Verification email not found in Mailpit');
  }

  const emailResponse = await page.request.get(`${MAILPIT_API}/message/${verificationEmail.ID}`);
  const emailData = await emailResponse.json();

  const emailBody = emailData.HTML || emailData.Text || '';
  const tokenMatch = emailBody.match(/[?&]token=([^"&\s<]+)/);
  if (!tokenMatch) {
    throw new Error('Verification token not found in email body');
  }
  const verificationToken = tokenMatch[1];

  // Step 4: Verify email via API
  const verifyResponse = await page.request.get(
    `${API_BASE}/auth/verify?token=${encodeURIComponent(verificationToken)}`
  );
  expect(verifyResponse.ok()).toBeTruthy();

  // Step 5: Log in via UI
  await page.goto('/login');
  await page.getByLabel('Email').fill(TEST_USER.email);
  await page.getByLabel('Password').fill(TEST_USER.password);
  await page.getByRole('button', { name: /sign in/i }).click();

  await page.waitForURL('**/dashboard');
  await expect(page.getByText('Personal Finance')).toBeVisible();

  await page.context().storageState({ path: 'apps/web/e2e/.auth/user.json' });
});
