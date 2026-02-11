import { test as setup, expect } from '@playwright/test';

const TEST_USER = {
  email: `e2e-test-${Date.now()}@example.com`,
  password: 'TestPass123#',
  displayName: 'E2E Test User',
};

const API_BASE = 'http://localhost:8000';
const MAILPIT_API = 'http://mailpit:8025/api/v1';

setup('authenticate', async ({ page }) => {
  // Step 1: Register via API (unique email per run)
  const registerResponse = await page.request.post(`${API_BASE}/auth/register`, {
    data: {
      email: TEST_USER.email,
      password: TEST_USER.password,
      display_name: TEST_USER.displayName,
    },
  });
  expect(registerResponse.status()).toBe(202);

  // Step 2: Get verification token from Mailpit (retry up to 10s for async job queue)
  let verificationEmail: { ID: string } | undefined;
  for (let attempt = 0; attempt < 10; attempt++) {
    await page.waitForTimeout(1000);
    const messagesResponse = await page.request.get(`${MAILPIT_API}/messages`);
    const messagesData = await messagesResponse.json();
    verificationEmail = messagesData.messages?.find(
      (msg: { To: Array<{ Address: string }>; Subject: string }) =>
        msg.To?.some((to: { Address: string }) => to.Address === TEST_USER.email) &&
        (msg.Subject?.includes('erif') || msg.Subject?.includes('onfirm')),
    );
    if (verificationEmail) break;
  }

  if (!verificationEmail) {
    throw new Error(`Verification email not found in Mailpit for ${TEST_USER.email} after 10s`);
  }

  const emailResponse = await page.request.get(`${MAILPIT_API}/message/${verificationEmail.ID}`);
  const emailData = await emailResponse.json();

  const emailBody = emailData.HTML || emailData.Text || '';
  const tokenMatch = emailBody.match(/[?&]token=([^"&\s<]+)/);
  if (!tokenMatch) {
    throw new Error('Verification token not found in email body');
  }
  const verificationToken = tokenMatch[1];

  // Step 3: Verify email via API
  const verifyResponse = await page.request.get(
    `${API_BASE}/auth/verify?token=${encodeURIComponent(verificationToken)}`,
  );
  expect(verifyResponse.ok()).toBeTruthy();

  // Step 4: Log in via UI
  await page.goto('/login');
  await page.getByLabel('Email address').fill(TEST_USER.email);
  await page.getByLabel('Password', { exact: true }).fill(TEST_USER.password);
  await page.getByRole('button', { name: /sign in/i }).click();

  await page.waitForURL('**/dashboard');
  await expect(page.getByRole('heading', { name: 'Personal Finance', exact: true })).toBeVisible();

  await page.context().storageState({ path: 'e2e/.auth/user.json' });
});
