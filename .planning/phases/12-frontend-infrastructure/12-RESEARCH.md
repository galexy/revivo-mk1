# Phase 12: Frontend Infrastructure - Research

**Researched:** 2026-02-10
**Domain:** React + Vite + Tailwind CSS v4 + shadcn/ui monorepo setup
**Confidence:** HIGH

## Summary

This phase sets up a modern React frontend infrastructure in an Nx monorepo using the latest stable releases: React 19.2, Vite 6/7, Tailwind CSS v4, and shadcn/ui with monorepo support. The research reveals three major architectural shifts from Claude's training data:

1. **Tailwind CSS v4's CSS-first configuration** - Eliminates tailwind.config.js in favor of @theme directives and @import "tailwindcss" in CSS files. This is a fundamental change requiring different setup patterns.

2. **shadcn/ui monorepo support** - Official CLI now understands monorepo structure with components.json configuration for shared libraries, eliminating previous manual path fixing.

3. **Nx inferred targets** - Modern Nx automatically detects tasks from tool configuration files (vite.config.ts, package.json), reducing manual project.json configuration.

The standard stack is well-established: Vite for build tooling (40x faster than CRA), Vitest for component tests (Jest-compatible, native Vite integration), Playwright for E2E, React Testing Library for user-centric testing, ESLint 9 with flat config, and Prettier for formatting. The pnpm migration is straightforward with `pnpm import` converting npm lock files automatically.

Critical pitfalls identified: Tailwind v4 requires Safari 16.4+/Chrome 111+/Firefox 128+ (no IE11), dark mode implementation differs from v3, PostCSS plugin moved to separate package, Vite proxy only works in dev (production needs real CORS), and shadcn/ui path aliases must match across components.json and tsconfig.

**Primary recommendation:** Use official Nx generators for React+Vite setup, leverage inferred targets, configure shadcn/ui for monorepo from the start, and implement Tailwind v4 CSS-first config with dark mode infrastructure from day one.

## Standard Stack

The established libraries/tools for React + Tailwind v4 + shadcn/ui in Nx monorepo:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2+ | UI framework | Latest stable (Dec 2024), RSC stable, Activity component |
| Vite | 6.0+ / 7.3+ | Build tool | 40x faster builds, native ESM, HMR in microseconds |
| Tailwind CSS | 4.0+ | Utility CSS | CSS-first config, 100x faster builds, modern browser features |
| TypeScript | 5.x | Type safety | Strict mode matches backend philosophy, bundler resolution |
| pnpm | Latest | Package manager | Better monorepo support, faster installs, stricter deps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn/ui | Latest | Component library | Monorepo-aware CLI, Tailwind v4 compatible, copy-paste components |
| Vitest | Latest | Component tests | Native Vite integration, Jest-compatible API, 10x faster |
| @testing-library/react | Latest | Component testing | User-centric queries, official React testing approach |
| Playwright | Latest | E2E tests | Modern browser automation, headless support |
| ESLint | 9.x | Linting | Flat config, typescript-eslint integration |
| Prettier | Latest | Formatting | Code formatting, integrates with ESLint via eslint-config-prettier |
| @nx/vite | Latest | Nx Vite plugin | Inferred targets, automatic caching |
| @nx/playwright | Latest | Nx Playwright plugin | E2E target configuration, task splitting |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vite | Webpack | Vite: faster dev, simpler config. Webpack: more mature, broader ecosystem |
| Vitest | Jest | Vitest: faster, Vite integration. Jest: more established, more resources |
| shadcn/ui | Material-UI | shadcn/ui: copy-paste ownership. MUI: pre-built, enterprise support |
| pnpm | npm/yarn | pnpm: stricter, faster. npm/yarn: more familiar, simpler hoisting |

**Installation:**
```bash
# Switch to pnpm first
pnpm import  # Converts package-lock.json to pnpm-lock.yaml
rm package-lock.json
pnpm install

# Core React + Vite (via Nx generator)
npx nx g @nx/react:application web --bundler=vite --routing=true --style=css --unitTestRunner=vitest --e2eTestRunner=playwright

# Tailwind CSS v4
pnpm add -D tailwindcss@next @tailwindcss/postcss@next

# shadcn/ui (monorepo-aware)
pnpm add -D shadcn@latest
npx shadcn@latest init

# Testing
pnpm add -D @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

# Fonts (self-hosted via Fontsource)
pnpm add @fontsource/inter @fontsource/jetbrains-mono

# ESLint + Prettier
pnpm add -D eslint@9 prettier eslint-config-prettier typescript-eslint

# TypeScript LSP for Claude Code
/plugin install vtsls@claude-code-lsps
```

## Architecture Patterns

### Recommended Project Structure
```
apps/web/
├── src/
│   ├── app/              # Application entry, routing
│   ├── features/         # Feature modules (Phase 13+)
│   ├── components/       # App-specific components
│   ├── lib/              # App utilities
│   ├── styles/           # Global styles, Tailwind imports
│   │   └── globals.css   # @import "tailwindcss" + @theme
│   └── main.tsx          # React entry point
├── tests/
│   ├── acceptance/       # Claude Code browser tests (markdown)
│   └── components/       # Vitest + RTL unit tests
├── e2e/                  # Playwright E2E tests
├── project.json          # Nx targets (mostly inferred)
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript config
├── postcss.config.js     # PostCSS + Tailwind v4
└── package.json          # Dependencies, scripts

libs/ui/
├── src/
│   ├── components/       # shadcn/ui components (Button, Card, etc.)
│   ├── hooks/            # Shared React hooks
│   ├── lib/              # utils.ts (cn helper, etc.)
│   └── index.ts          # Barrel export
├── components.json       # shadcn/ui monorepo config
├── tsconfig.json         # Library TypeScript config
└── package.json          # main: "./src/index.ts" (no build)

tsconfig.base.json        # Root with path aliases
pnpm-workspace.yaml       # pnpm workspace config
```

### Pattern 1: Tailwind CSS v4 CSS-First Configuration
**What:** Define design tokens in CSS using @theme directive instead of tailwind.config.js
**When to use:** All Tailwind v4 projects
**Example:**
```css
/* apps/web/src/styles/globals.css */
@import "tailwindcss";

@theme {
  /* Color palette - finance-appropriate */
  --color-primary: #2563eb;
  --color-secondary: #64748b;
  --color-success: #10b981;
  --color-danger: #ef4444;
  --color-warning: #f59e0b;

  /* Typography */
  --font-family-sans: "Inter", system-ui, sans-serif;
  --font-family-mono: "JetBrains Mono", monospace;

  /* Spacing - balanced density */
  --spacing-tight: 0.5rem;
  --spacing-normal: 1rem;
  --spacing-relaxed: 1.5rem;
}

/* Dark mode CSS variables */
:root {
  --background: hsl(0 0% 100%);
  --foreground: hsl(222.2 84% 4.9%);
}

.dark {
  --background: hsl(222.2 84% 4.9%);
  --foreground: hsl(210 40% 98%);
}
```
**Source:** [Tailwind CSS v4.0 Blog](https://tailwindcss.com/blog/tailwindcss-v4)

### Pattern 2: shadcn/ui Monorepo Configuration
**What:** Configure components.json to install components in shared libs/ui package
**When to use:** When using shadcn/ui in monorepo with shared component library
**Example:**
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "apps/web/src/styles/globals.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@workspace/ui/components",
    "utils": "@workspace/ui/lib/utils",
    "ui": "@workspace/ui/components",
    "lib": "@workspace/ui/lib",
    "hooks": "@workspace/ui/hooks"
  }
}
```
**Source:** [shadcn/ui Monorepo Docs](https://ui.shadcn.com/docs/monorepo)

### Pattern 3: Internal Package (No Build Step)
**What:** libs/ui package.json points to raw .ts source, Vite transpiles directly
**When to use:** Shared UI library in monorepo
**Example:**
```json
{
  "name": "@workspace/ui",
  "version": "0.0.0",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./components/*": "./src/components/*.tsx",
    "./hooks/*": "./src/hooks/*.ts",
    "./lib/*": "./src/lib/*.ts"
  }
}
```
**Source:** [Internal Packages Pattern](https://turborepo.dev/blog/you-might-not-need-typescript-project-references)

### Pattern 4: Nx Inferred Targets
**What:** Nx automatically detects build/serve/test/lint targets from vite.config.ts
**When to use:** All Nx + Vite projects
**Example:**
```typescript
// apps/web/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin';

export default defineConfig({
  plugins: [react(), nxViteTsPaths()],
  server: {
    port: 5173,
    host: 'localhost',
  },
  preview: {
    port: 4300,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.ts',
  },
});
```
**Result:** Nx infers build, serve, preview, test targets automatically
**Source:** [Nx Inferred Tasks](https://nx.dev/docs/concepts/inferred-tasks)

### Pattern 5: FastAPI CORS for Development
**What:** Add CORSMiddleware to FastAPI allowing localhost:5173 origin
**When to use:** When React dev server needs to call FastAPI backend
**Example:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Source:** [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)

### Pattern 6: pnpm Workspace Configuration
**What:** pnpm-workspace.yaml defines monorepo packages with glob patterns
**When to use:** When migrating from npm to pnpm in Nx monorepo
**Example:**
```yaml
packages:
  - 'apps/*'
  - 'libs/*'
```
**Note:** Nx manages workspace structure, pnpm-workspace.yaml just needs to include all packages

### Pattern 7: React Testing Library Component Tests
**What:** Test components by user behavior using getByRole queries
**When to use:** All component unit tests
**Example:**
```typescript
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { Button } from './button';

test('button handles click', async () => {
  const handleClick = vi.fn();
  render(<Button onClick={handleClick}>Click me</Button>);

  const button = screen.getByRole('button', { name: /click me/i });
  await userEvent.click(button);

  expect(handleClick).toHaveBeenCalledTimes(1);
});
```
**Source:** [React Testing Library Best Practices](https://testing-library.com/docs/react-testing-library/intro/)

### Pattern 8: Self-Hosted Fonts
**What:** Use Fontsource packages for Inter and JetBrains Mono, import in CSS
**When to use:** When self-hosting fonts for performance and privacy
**Example:**
```typescript
// apps/web/src/main.tsx
import '@fontsource/inter/400.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/700.css';
```
**Benefits:** Self-hosting avoids render-blocking third-party requests, doubles performance
**Source:** [Fontsource Inter](https://fontsource.org/fonts/inter/install)

### Anti-Patterns to Avoid
- **Don't hand-write tailwind.config.js** - Tailwind v4 uses CSS-first @theme directives
- **Don't use Vite proxy in production** - Proxy only works in dev, use real CORS for production
- **Don't install shadcn/ui components before monorepo setup** - Configure components.json first
- **Don't use wildcard CORS origins in production** - Development uses specific origins
- **Don't manually configure Nx targets for standard tasks** - Let plugins infer build/test/serve
- **Don't import from @workspace/ui/src/* in apps** - Use path aliases from components.json
- **Don't mix @tailwindcss/postcss with v3 config** - v4 PostCSS plugin is separate package

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS utility classes | Custom utility class system | Tailwind CSS v4 | Purging, responsive variants, dark mode, 100x faster builds |
| UI components | Custom button/card/input components | shadcn/ui | Accessibility, variants, dark mode, copy-paste ownership |
| Component testing | Custom render helpers | React Testing Library | User-centric queries, accessibility, best practices |
| Build tooling | Custom webpack config | Vite + @nx/vite | HMR in microseconds, auto-inferred targets, caching |
| Font loading | Manual @font-face declarations | Fontsource packages | Optimized subsets, weight/style variants, maintained |
| CORS in development | Custom proxy server | Vite proxy + FastAPI CORS | Zero config, automatic in dev, clear production path |
| Dark mode toggle | Custom CSS variable switching | Tailwind v4 dark mode + class toggle | Prefers-color-scheme, localStorage sync, utility integration |
| Monospace font alignment | Custom CSS padding | JetBrains Mono | Designed for code/numbers, tabular figures, better alignment |
| Path aliases | Relative imports ../../../ | TypeScript paths + Nx | Type-safe, refactor-safe, cleaner imports |
| Task caching | Custom build cache | Nx computation cache | Distributed, content-based, works across CI/local |

**Key insight:** The modern React+Vite+Tailwind v4 ecosystem is mature and optimized. Custom solutions for these problems will have worse performance, accessibility, and maintenance than using established tools. The biggest shift is Tailwind v4's CSS-first approach - don't try to adapt v3 JavaScript config patterns.

## Common Pitfalls

### Pitfall 1: Tailwind v4 Browser Support Requirements
**What goes wrong:** Application breaks in older browsers due to modern CSS features
**Why it happens:** Tailwind v4 uses cascade layers, @property, color-mix() requiring modern browsers
**How to avoid:** Document browser requirements upfront: Safari 16.4+, Chrome 111+, Firefox 128+. If older browser support needed, stay on Tailwind v3.
**Warning signs:** CSS not applying, JavaScript errors about unsupported features
**Source:** [Tailwind CSS v4 Upgrade Guide](https://github.com/tailwindlabs/tailwindcss/discussions/16517)

### Pitfall 2: Tailwind v4 Dark Mode Not Working
**What goes wrong:** Dark mode utilities don't apply, theme doesn't switch
**Why it happens:** v4 dark mode implementation differs from v3, requires explicit configuration
**How to avoid:** Use data-theme or class-based dark mode selector, update HTML element attribute/class, sync to localStorage
**Warning signs:** dark: prefix utilities not applying, theme stuck in light mode
**Code example:**
```typescript
// Dark mode toggle
const toggleDark = () => {
  const html = document.documentElement;
  const isDark = html.classList.contains('dark');
  html.classList.toggle('dark', !isDark);
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
};
```
**Source:** [Tailwind v4 Dark Mode Discussion](https://github.com/tailwindlabs/tailwindcss/discussions/15083)

### Pitfall 3: PostCSS Plugin for Tailwind v4 Missing
**What goes wrong:** Build fails with "unknown @import directive" or Tailwind not processing
**Why it happens:** Tailwind v4 PostCSS plugin moved to separate package @tailwindcss/postcss
**How to avoid:** Install @tailwindcss/postcss@next, update postcss.config.js
**Code example:**
```javascript
// postcss.config.js
module.exports = {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};
```
**Source:** [Tailwind v4 Migration Issues](https://github.com/tailwindlabs/tailwindcss/discussions/16642)

### Pitfall 4: shadcn/ui Components in Wrong Location
**What goes wrong:** CLI installs components in apps/web/src/@workspace/ui/ instead of libs/ui/
**Why it happens:** components.json aliases misconfigured before running shadcn init
**How to avoid:** Configure components.json with correct paths BEFORE adding components. Verify aliases match tsconfig.base.json paths.
**Warning signs:** Duplicate component folders, import errors, path not found
**Source:** [shadcn/ui Monorepo Issues](https://github.com/shadcn-ui/ui/discussions/6162)

### Pitfall 5: Vite Proxy Only Works in Development
**What goes wrong:** Production build makes direct API calls that fail CORS
**Why it happens:** Vite proxy configuration only works during dev server (vite dev)
**How to avoid:** Add CORSMiddleware to FastAPI backend for production. Use environment variables for API base URL.
**Code example:**
```typescript
// Use env var for API base
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```
**Source:** [Vite CORS Proxy Guide](https://medium.com/@kam96.5.20/resolving-cors-issues-in-react-applications-with-vite-0d78753ca12d)

### Pitfall 6: pnpm Strict Dependency Resolution Breaking Builds
**What goes wrong:** Build fails with "module not found" for transitive dependencies
**Why it happens:** pnpm doesn't hoist dependencies like npm, uses symlinks for strict resolution
**How to avoid:** Explicitly declare ALL direct dependencies in package.json, don't rely on hoisting
**Warning signs:** "Cannot find module X" where X worked with npm but not pnpm
**Source:** [pnpm Limitations](https://pnpm.io/limitations)

### Pitfall 7: ESLint 9 Flat Config Not Recognized
**What goes wrong:** ESLint config not loading, rules not applying
**Why it happens:** ESLint 9 uses flat config (eslint.config.mjs) instead of .eslintrc
**How to avoid:** Create eslint.config.mjs, use defineConfig() for type safety, import plugins correctly
**Code example:**
```javascript
// eslint.config.mjs
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import react from 'eslint-plugin-react';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.strict,
  react.configs.flat.recommended,
  prettier,
);
```
**Source:** [ESLint 9 Flat Config](https://eslint.org/blog/2025/03/flat-config-extends-define-config-global-ignores/)

### Pitfall 8: Prettier and ESLint Formatting Conflicts
**What goes wrong:** ESLint errors contradict Prettier formatting, unfixable conflicts
**Why it happens:** ESLint formatting rules enabled alongside Prettier
**How to avoid:** Use eslint-config-prettier to disable conflicting rules, run Prettier separately
**Rule:** ESLint for correctness, Prettier for formatting (never mix)
**Source:** [Prettier ESLint Integration](https://prettier.io/docs/integrating-with-linters)

### Pitfall 9: React 19 Breaking Changes
**What goes wrong:** Build errors, runtime warnings about deprecated APIs
**Why it happens:** React 19 removed legacy APIs, changed component lifecycle
**How to avoid:** Review React 19 migration guide, update deprecated patterns, test thoroughly
**Warning signs:** Warnings about deprecated APIs, prop types errors
**Note:** shadcn/ui components updated for React 19 compatibility
**Source:** [React v19 Release](https://react.dev/blog/2024/12/05/react-19)

### Pitfall 10: Nx Inferred Targets Not Appearing
**What goes wrong:** npx nx show project web shows empty targets
**Why it happens:** Missing @nx/vite plugin or vite.config.ts not detected
**How to avoid:** Install @nx/vite, ensure vite.config.ts exists, check nx.json plugins array
**Verification:** Run npx nx show project web to see inferred targets
**Source:** [Nx Inferred Tasks](https://nx.dev/docs/concepts/inferred-tasks)

## Code Examples

Verified patterns from official sources:

### Example 1: Vite Config for React + TypeScript
```typescript
// apps/web/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin';

export default defineConfig({
  root: __dirname,
  cacheDir: '../../node_modules/.vite/apps/web',

  plugins: [
    react(),
    nxViteTsPaths(), // Nx TypeScript path mapping
  ],

  server: {
    port: 5173,
    host: 'localhost',
  },

  preview: {
    port: 4300,
    host: 'localhost',
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
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    reporters: ['default'],
    coverage: {
      reportsDirectory: '../../coverage/apps/web',
      provider: 'v8',
    },
  },
});
```
**Source:** [Nx Vite Configuration](https://nx.dev/nx-api/vite/generators/configuration)

### Example 2: Vitest Setup File
```typescript
// apps/web/src/test-setup.ts
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest expect with jest-dom matchers
expect.extend(matchers);

// Cleanup after each test
afterEach(() => {
  cleanup();
});
```
**Source:** [Vitest with React Testing Library](https://vitest.dev/guide/browser/component-testing)

### Example 3: TypeScript Path Aliases
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@workspace/ui": ["libs/ui/src/index.ts"],
      "@workspace/ui/*": ["libs/ui/src/*"],
      "@/*": ["apps/web/src/*"]
    }
  }
}
```
**Source:** [Nx TypeScript Project Linking](https://nx.dev/docs/concepts/typescript-project-linking)

### Example 4: Playwright E2E Test
```typescript
// apps/web/e2e/smoke.spec.ts
import { test, expect } from '@playwright/test';

test('app loads without errors', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // Check for app render
  await expect(page).toHaveTitle(/Finance/);

  // Check no console errors
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await page.waitForLoadState('networkidle');
  expect(errors).toHaveLength(0);
});
```
**Source:** [Playwright Nx Setup](https://nx.dev/docs/technologies/test-tools/playwright)

### Example 5: shadcn/ui Component Usage
```typescript
// apps/web/src/features/auth/login.tsx
import { Button } from '@workspace/ui/components/button';
import { Card, CardHeader, CardTitle, CardContent } from '@workspace/ui/components/card';
import { Input } from '@workspace/ui/components/input';
import { Label } from '@workspace/ui/components/label';

export function LoginForm() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Login</CardTitle>
      </CardHeader>
      <CardContent>
        <form>
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" />
            </div>
            <Button type="submit">Sign In</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
```
**Source:** [shadcn/ui Components](https://ui.shadcn.com/docs/components/radix/button)

### Example 6: Dark Mode Toggle
```typescript
// libs/ui/src/hooks/use-theme.ts
import { useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>('system');

  useEffect(() => {
    const stored = localStorage.getItem('theme') as Theme;
    if (stored) setTheme(stored);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark');

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }

    localStorage.setItem('theme', theme);
  }, [theme]);

  return { theme, setTheme };
}
```
**Source:** [Tailwind Dark Mode](https://tailwindcss.com/docs/dark-mode)

### Example 7: Claude Code Acceptance Test
```markdown
<!-- apps/web/tests/acceptance/01-app-loads.md -->
# Acceptance Test: App Loads Successfully

## Prerequisites
- API server running on http://localhost:8000
- Web server running on http://localhost:5173

## Steps
1. Navigate to http://localhost:5173
2. Verify page title contains "Finance"
3. Verify no console errors
4. Verify app renders without blank screen
5. Verify Inter font loaded (inspect computed styles)

## Expected Result
- App displays without errors
- No blank screens or loading spinners stuck
- No network errors in console
- Custom fonts applied (not system fallback)
```
**Note:** Claude Code reads and executes these steps via Chrome integration

### Example 8: ESLint + Prettier Configuration
```javascript
// eslint.config.mjs
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooks,
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off', // Not needed with React 19
    },
  },
  prettier, // Must be last to override formatting rules
);
```
**Source:** [ESLint 9 with TypeScript](https://typescript-eslint.io/getting-started/)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tailwind.config.js | @theme in CSS | Tailwind v4 (Jan 2025) | No JS config, faster builds, CSS-first |
| Create React App | Vite | ~2021-2022 | 40x faster builds, native ESM, better DX |
| Jest | Vitest | ~2022-2023 | 10x faster, native Vite integration |
| .eslintrc | eslint.config.mjs | ESLint 9 (2024) | Flat config, type-safe, simpler |
| npm/yarn | pnpm | ~2023-2024 | Faster, stricter, better monorepo |
| Manual shadcn setup | Monorepo CLI | shadcn v2 (2024) | Automatic path handling, components.json |
| Nx manual targets | Inferred targets | Nx 18 (2024) | Auto-detect from tool configs |
| React 18 | React 19 | Dec 2024 | RSC stable, Activity component, better perf |
| Tailwind v3 dark mode | CSS variables + class | Tailwind v4 (2025) | More flexible, better SSR |

**Deprecated/outdated:**
- **Create React App** - Unmaintained, replaced by Vite
- **tailwind.config.js** - v4 uses CSS @theme directives
- **ESLint .eslintrc** - v9 uses flat config
- **@tailwind base/components/utilities** - v4 uses @import "tailwindcss"
- **tailwindcss-animate** - shadcn/ui now uses tw-animate-css
- **Manual Nx target definitions** - Plugins infer from vite.config.ts
- **package-lock.json** - pnpm uses pnpm-lock.yaml

## Open Questions

Things that couldn't be fully resolved:

1. **Exact color palette for finance UI**
   - What we know: Should be professional, appropriate for finance, balanced density
   - What's unclear: Specific hex values for primary/secondary/accent colors
   - Recommendation: Use Tailwind's default slate/blue palette initially, refine in Phase 13 with user feedback

2. **Vite exact version (6 vs 7)**
   - What we know: Vite 6 stable released, Vite 7 already exists (7.3.1 latest)
   - What's unclear: Which version Nx @nx/vite generator defaults to
   - Recommendation: Accept Nx generator default, both versions work. Vite 7 has Environment API improvements.

3. **Claude Code TypeScript LSP plugin name**
   - What we know: Official plugin incomplete, vtsls@claude-code-lsps recommended alternative
   - What's unclear: Whether official typescript-lsp fixed since GitHub issues filed
   - Recommendation: Use vtsls@claude-code-lsps (verified working), fallback to official if preferred

4. **Exact monospace font**
   - What we know: JetBrains Mono good for numbers, separate from UI font
   - What's unclear: User preference between JetBrains Mono, Fira Code, Roboto Mono
   - Recommendation: JetBrains Mono (designed for code/numbers, tabular figures), easy to swap later

5. **Playwright CI integration timing**
   - What we know: Deferred until real UI features exist
   - What's unclear: Which future phase will add CI
   - Recommendation: Keep Playwright local-only for now, add to CI when Phase 13+ adds testable features

## Sources

### Primary (HIGH confidence)
- [Tailwind CSS v4.0 - Official Blog](https://tailwindcss.com/blog/tailwindcss-v4)
- [shadcn/ui Tailwind v4 Docs](https://ui.shadcn.com/docs/tailwind-v4)
- [shadcn/ui Monorepo Docs](https://ui.shadcn.com/docs/monorepo)
- [Nx Inferred Tasks](https://nx.dev/docs/concepts/inferred-tasks)
- [Nx Vite Plugin](https://nx.dev/nx-api/vite/generators/configuration)
- [Nx Playwright Plugin](https://nx.dev/docs/technologies/test-tools/playwright)
- [React v19 Release Notes](https://react.dev/blog/2024/12/05/react-19)
- [Vite 6.0 Release](https://vite.dev/blog/announcing-vite6)
- [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [pnpm Import Command](https://pnpm.io/cli/import)
- [Fontsource Inter](https://fontsource.org/fonts/inter/install)
- [ESLint Flat Config](https://eslint.org/blog/2025/03/flat-config-extends-define-config-global-ignores/)
- [Prettier ESLint Integration](https://prettier.io/docs/integrating-with-linters)

### Secondary (MEDIUM confidence)
- [Tailwind v4 Migration Guide](https://medium.com/@oumuamuaa/transitioning-from-tailwind-config-js-to-css-first-in-tailwind-css-v4-4afb3bfca4ee) - WebSearch verified with official docs
- [Vite + React TypeScript Setup Guide](https://medium.com/@robinviktorsson/complete-guide-to-setting-up-react-with-typescript-and-vite-2025-468f6556aaf2) - WebSearch verified
- [Nx React Vite Tutorial](https://nx.dev/blog/react-vite-and-typescript-get-started-in-under-2-minutes) - Official Nx blog
- [shadcn/ui Nx Integration](https://medium.com/@sakshijaiswal0310/building-a-scalable-react-monorepo-with-nx-and-shadcn-ui-a-complete-implementation-guide-96c2bb1b42e8) - Community guide
- [Vitest RTL Setup](https://victorbruce82.medium.com/vitest-with-react-testing-library-in-react-created-with-vite-3552f0a9a19a) - Community guide
- [pnpm Migration Guide](https://medium.com/@jathushan-r/optimizing-nx-monorepos-with-pnpm-a-developers-guide-4c37b6c084a6) - WebSearch verified

### Tertiary (LOW confidence - needs validation)
- [Claude Code LSP Plugins Testing](https://medium.com/@joe.njenga/i-tested-all-available-claude-code-lsp-plugins-dont-waste-time-read-this-first-6896e992a540) - Single community source, recommends vtsls
- [Tailwind v4 with shadcn monorepo](https://github.com/fuma-nama/fumadocs/discussions/1338) - GitHub discussion, needs official verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official docs and stable releases for all tools
- Architecture: HIGH - Nx and shadcn/ui official monorepo guidance
- Tailwind v4 CSS-first: HIGH - Official Tailwind docs, verified breaking change
- Pitfalls: MEDIUM-HIGH - Mix of official docs and recent community experience (2025-2026)
- Version numbers: HIGH - Official release pages, npm package info

**Research date:** 2026-02-10
**Valid until:** ~30 days (stable ecosystem, but fast-moving tools like Vite)

**Key uncertainties resolved:**
- Tailwind v4 CSS-first config is stable and official approach
- shadcn/ui monorepo support is official CLI feature
- Nx inferred targets are production-ready since v18
- React 19 and Vite 6/7 are stable releases

**Areas requiring judgment during planning:**
- Exact color palette (Claude's discretion per CONTEXT.md)
- Vite 6 vs 7 (accept generator default)
- ESLint rule specifics (start with strict, relax if needed)
- Monospace font choice (JetBrains Mono recommended but flexible)
