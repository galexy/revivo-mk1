# Phase 12: Frontend Infrastructure - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up frontend tooling, testing infrastructure, and developer experience for the React app. This phase delivers a working React app with Tailwind CSS v4, shadcn/ui component library, Playwright for smoke tests, Vitest + RTL for component tests, and Claude Code Chrome integration for UI acceptance testing. No UI features are built — those are Phase 13+.

</domain>

<decisions>
## Implementation Decisions

### Component Conventions
- Balanced density — moderate spacing but good use of space; dense when it makes sense (e.g., transaction tables)
- Dark mode from day one — CSS variables and theme toggle infrastructure so all components are built dark-mode-ready
- Color palette: Claude's discretion (pick something appropriate for a finance app)
- Font: Inter (explicit, loaded/self-hosted) for UI text
- Separate monospace font (e.g., JetBrains Mono) for financial figures (balances, amounts) — better column alignment
- Left sidebar navigation — persistent sidebar with account list and nav items (like Quicken, YNAB)
- Negative amounts: red text with minus sign (-$50.00), not parentheses
- Desktop-first, responsive — primary target is desktop/laptop; sidebar collapses on mobile, tables scroll horizontally
- `@/` prefix for path aliases (standard shadcn/ui convention)

### Dev Workflow & Proxying
- Direct CORS — frontend calls API on different port, CORS middleware configured on FastAPI backend
- Add CORSMiddleware to FastAPI allowing localhost:5173 in dev as part of this phase
- Vite dev server runs via `npx nx serve web` (same pattern as `npx nx serve api`), NOT a Docker Compose service
- Port 5173 (Vite default) for frontend dev server, API stays on 8000
- Frontend and API serve targets are independent — developer runs both manually, no Nx dependency between them

### Tooling & Linting
- ESLint + Prettier for frontend linting and formatting
- TypeScript strict mode (`strict: true` in tsconfig) — matches backend's pyright strict philosophy
- Full Nx target suite for web project: test, lint, typecheck, format, serve, e2e — matches api/domain pattern, CI picks them up via `nx affected`

### Package Manager & TypeScript Config
- Switch from npm to pnpm — better monorepo support, faster installs, stricter dependency resolution
- Internal package pattern for libs/ui — `main` and `types` in package.json point to raw `.ts` source (e.g., `./src/index.ts`)
- No build step for libs/ui — Vite transpiles directly
- TypeScript path aliases in `tsconfig.base.json` for cross-project imports (Nx-supported approach)
- `moduleResolution: "bundler"` — modern, works with Vite natively

### shadcn/ui Monorepo Integration
- Follow official shadcn/ui monorepo guidance (https://ui.shadcn.com/docs/monorepo)
- Components live in libs/ui/ — shared library consumed by apps/web
- components.json configured for monorepo with aliases pointing to the ui package
- Tailwind CSS v4 with CSS-first configuration (@theme directives, no tailwind.config.js)
- Install minimal starter component set: Button, Card, Input, Label, Form — enough to verify setup and prep for Phase 13 (Login UI)

### Testing Strategy
- Vitest for component unit tests (native Vite integration)
- React Testing Library (@testing-library/react) included from day one
- Playwright for smoke test — verify app renders without JS errors (just "app loads" scope at this phase)
- Playwright e2e target on the web project itself (not a separate apps/web-e2e project)
- Playwright local only for now — skip CI integration until real UI features exist
- No Storybook at this stage

### UI Acceptance Testing (Claude Code + Chrome)
- Acceptance tests are persistent, repeatable test scenarios — not ad-hoc verification
- Test scenarios written as markdown files in `apps/web/tests/acceptance/`
- Natural language test steps that Claude Code reads and executes via Chrome integration (`claude --chrome`)
- Tests run against real API (both API and web servers must be running)
- NOT Playwright scripts — Claude Code drives the browser via Chrome DevTools integration
- Build a repository of these test scenarios incrementally as UI features are added

### TypeScript LSP for Claude Code
- Install official TypeScript LSP plugin: `/plugin install typescript-lsp@claude-plugins-official`
- Gives Claude Code real-time diagnostics, go-to-definition, find references while coding
- Eliminates need to run full typecheck after every edit — errors visible immediately

### Claude's Discretion
- Color palette selection (finance-appropriate)
- Exact shadcn/ui theme customization details
- Vite configuration details
- ESLint/Prettier rule specifics
- Exact monospace font choice for financial figures
- pnpm migration technical approach (lock file conversion, CI updates)

</decisions>

<specifics>
## Specific Ideas

- "I want it like Quicken/YNAB" — left sidebar with account tree, dense transaction tables
- Internal packages pattern from Turborepo blog: https://turborepo.dev/blog/you-might-not-need-typescript-project-references
- shadcn/ui monorepo docs: https://ui.shadcn.com/docs/monorepo
- Nx TypeScript project linking: https://nx.dev/docs/concepts/typescript-project-linking
- Claude Code Chrome integration for UAT: https://code.claude.com/docs/en/chrome
- Acceptance tests should be continuously runnable (like integration tests), not just at verify stage

</specifics>

<deferred>
## Deferred Ideas

- Storybook for component development — add when component library grows
- Playwright CI integration — add when real UI features exist to test
- Claude Code GSD skills for browser-driven UAT — future automation, start with manual test scenarios first
- Mobile-specific layouts — desktop-first for now, full mobile support later

</deferred>

---

*Phase: 12-frontend-infrastructure*
*Context gathered: 2026-02-09*
