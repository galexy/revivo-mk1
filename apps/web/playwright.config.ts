import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env['CI'],
  retries: process.env['CI'] ? 2 : 0,
  workers: process.env['CI'] ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
      use: {
        launchOptions: {
          executablePath: '/usr/bin/chromium',
          args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
        },
      },
    },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        headless: true,
        storageState: 'e2e/.auth/user.json',
        launchOptions: {
          executablePath: '/usr/bin/chromium',
          args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
        },
      },
      dependencies: ['setup'],
    },
  ],
});
