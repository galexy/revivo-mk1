# Phase 14: Frontend API & Routing - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish patterns for API communication and client-side routing. TanStack Query for server state management, type-safe API client from OpenAPI spec, consistent error handling patterns, and Playwright e2e tests updated for auth. TanStack Router and Axios interceptors already exist from Phase 13 — this phase adds the data layer and patterns that all future UI phases (15-26) build on.

</domain>

<decisions>
## Implementation Decisions

### Error & Feedback Patterns
- **Error display strategy:** Context-dependent — inline banners for form validation/submission errors, toast notifications for background failures (e.g., data refresh failed)
- **Success feedback for mutations:** Desktop-app feel — inline edits (transaction register) should feel like editing a cell in Google Sheets with auto-save and a subtle hint of success (not disruptive toasts). For non-inline actions (create account, delete), Claude decides per action whether toast+navigate or navigate-only is more appropriate based on whether the action has a natural destination
- **Backend error messages:** Hybrid approach — use backend messages directly for validation errors (they're specific and actionable), friendly translated messages for server errors (user can't act on "Internal Server Error")
- **Client-side validation:** Both layers — client-side (zod) for instant feedback, server-side as authoritative source
- **Background refresh failures:** Subtle status indicator in header/status bar showing connection state (like Slack's yellow banner), not disruptive toasts
- **Destructive action confirmation:** Severity-dependent — undo toast pattern for low-cost actions (delete transaction), confirmation dialog for high-cost actions (delete account)
- **Detailed error handling semantics** (4xx vs 5xx visual distinction, session expiry flow) deferred to Phase 16/17 when actual UI is being built

### Data Loading UX
- **Loading states:** Skeleton loaders for list/table views (many items), spinner for single-item detail views
- **Cache behavior:** Claude's discretion — pick sensible stale times per data type (accounts rarely change, transactions change more often). Use stale-while-revalidate pattern (show cached data immediately, refresh in background)
- **Background refresh visual cue:** Claude's discretion on whether to silently update or briefly highlight changed values
- **Manual refresh:** Support both pull-to-refresh on mobile viewports and a refresh button on desktop. User always has explicit control

### REST API Calling & Client-Side State Management
- **API client:** Generated from OpenAPI spec — auto-generate TypeScript types/client from backend's /openapi.json so types stay in sync with backend automatically
- **State management layers:**
  - Server state: TanStack Query (accounts, transactions, user profile)
  - Auth state: React Context (existing AuthContext — token, login/logout, isAuthenticated)
  - URL state: TanStack Router (existing — current route, selected account, filters)
  - Local UI state: useState (form inputs, modals, dropdowns)
  - No global client store needed (no Zustand/Redux). Revisit only if a concrete need arises
- **URL vs React state:** Hybrid — URL for major navigation state (which account, date range, filters), React state for ephemeral UI state (dropdown open, edit mode)
- **Optimistic updates:** Context-dependent — inline edits (transaction fields) use optimistic updates for desktop-app feel, create/delete actions wait for server confirmation
- **Prefetching:** Deferred to a future phase. No hover/focus prefetching in Phase 14
- **Query organization:** Claude's discretion — queryOptions factories (TkDodo's v5 pattern) or custom hooks, whichever best fits TanStack Router integration

### Claude's Discretion
- Subtle save confirmation indicator for inline editing (cell highlight, checkmark, etc.)
- Per-action success feedback pattern (toast+navigate vs navigate-only)
- Query stale time configuration per data type
- Background refresh visual cue approach
- queryOptions factory vs custom hook organization pattern
- OpenAPI codegen tooling choice (openapi-typescript, orval, etc.)
- TanStack Query default configuration (retry count, refetchOnWindowFocus, gcTime)

</decisions>

<specifics>
## Specific Ideas

- "Updating or saving a transaction should feel like I'm just editing a cell in Google Sheets" — the transaction register view should auto-save on blur/navigate-away with minimal visual feedback
- Desktop-app feel is a core aesthetic goal — the app should feel responsive and native, not web-form-ish
- TanStack Query architecture follows TkDodo's recommended patterns (maintainer's blog): feature-based query organization, query key hierarchy for smart invalidation, queryOptions API as primary abstraction
- Route loaders prefetch data so navigation feels instant (no loading spinners between pages)
- Existing Axios interceptors handle auth token injection and refresh — all queryFn implementations use the project's `api` instance

</specifics>

<deferred>
## Deferred Ideas

- Hover/focus prefetching for navigation links — future optimization phase
- Detailed error handling semantics (4xx vs 5xx visual distinction, session expiry UX) — Phase 16/17
- Zustand/Redux global client store — only if a concrete need arises in a future phase

</deferred>

---

*Phase: 14-frontend-api-routing*
*Context gathered: 2026-02-11*
