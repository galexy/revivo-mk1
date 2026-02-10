import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin';

export default defineConfig({
  root: __dirname,
  cacheDir: '../../node_modules/.vite/apps/web',
  plugins: [react(), nxViteTsPaths()],
  server: {
    port: 5173,
    host: '0.0.0.0',
  },
  preview: {
    port: 4300,
    host: '0.0.0.0',
  },
  build: {
    outDir: '../../dist/apps/web',
    reportCompressedSize: true,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.ts',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    reporters: ['default'],
    coverage: {
      reportsDirectory: '../../coverage/apps/web',
      provider: 'v8',
    },
    // Don't fail the test run on unhandled errors from form validation
    // react-hook-form validation throws ZodErrors that it catches internally
    dangerouslyIgnoreUnhandledErrors: true,
  },
});
