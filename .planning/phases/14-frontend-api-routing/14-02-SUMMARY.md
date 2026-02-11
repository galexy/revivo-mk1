---
phase: 14-frontend-api-routing
plan: 02
subsystem: ui
tags: [tanstack-query, react-query, openapi-typescript, axios, type-safety]

# Dependency graph
requires:
  - phase: 14-01
    provides: OpenAPI type generation with openapi-typescript v7
  - phase: 13-login-ui
    provides: Axios instance with token refresh interceptor
provides:
  - TanStack Query infrastructure with QueryClient configuration
  - Type-safe API client wrapping Axios with generated OpenAPI types
  - Query key factory with hierarchical structure for cache invalidation
  - queryOptions factories for accounts, transactions, categories
  - API error parsing utilities for consistent error handling
  - Route loader pattern using ensureQueryData for instant navigation
affects: [15-account-list-ui, 16-transaction-list-ui, 17-category-ui, frontend-data-layer]

# Tech tracking
tech-stack:
  added:
    - "@tanstack/react-query": "Query client and data fetching"
    - "@tanstack/react-query-devtools": "Development debugging tools"
  patterns:
    - "Query key hierarchy: [entity, scope, ...params] for smart invalidation"
    - "queryOptions factories: define once, use in loaders and components"
    - "Route loaders with ensureQueryData for instant navigation"
    - "API error parsing: handle FastAPI string and object detail formats"

key-files:
  created:
    - apps/web/src/lib/query-client.ts: "QueryClient with configured defaults"
    - apps/web/src/lib/query-keys.ts: "Hierarchical query key factory"
    - apps/web/src/lib/api-client.ts: "Type-safe API wrapper with generated types"
    - apps/web/src/lib/query-options.ts: "queryOptions factories for entities"
    - apps/web/src/lib/api-error.ts: "API error parsing utilities"
  modified:
    - apps/web/src/main.tsx: "Added QueryClientProvider wrapper"
    - apps/web/src/routes.tsx: "Added queryClient to router context, loader example"

key-decisions:
  - "QueryClient stale times: 30s default, 60s accounts, 15s transactions, 5min categories"
  - "QueryClientProvider wraps AuthProvider (so auth context can use queries if needed)"
  - "Auth context stays React Context (not migrated to TanStack Query)"
  - "API client unwraps AxiosResponse.data for cleaner function signatures"
  - "Route loader pattern: ensureQueryData returns cached if fresh, fetches if stale"

patterns-established:
  - "Query keys: TkDodo v5 hierarchical pattern with entity.all → lists() → list(filters)"
  - "API client: type-safe functions using components['schemas']['TypeName'] from generated types"
  - "Error handling: parseApiError handles both string detail and object detail from FastAPI"
  - "Route loaders: prefetch data in loader using queryOptions + ensureQueryData"

# Metrics
duration: 5min
completed: 2026-02-11
---

# Phase 14 Plan 02: TanStack Query Infrastructure Summary

**TanStack Query integrated with type-safe API client, hierarchical query keys, queryOptions factories, and route loader pattern for instant navigation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-11T05:43:45Z
- **Completed:** 2026-02-11T05:48:32Z
- **Tasks:** 2
- **Files created:** 5
- **Files modified:** 3

## Accomplishments

- QueryClient configured with sensible defaults (30s staleTime, 5min gcTime, retry logic excluding 401s)
- Type-safe API client wraps existing Axios instance with generated OpenAPI types
- Query key factory supports entity-based cache invalidation
- queryOptions factories ready for route loaders and components
- API error parsing handles both FastAPI error formats consistently
- Route loader pattern demonstrated on dashboard route for instant navigation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create QueryClient, query keys, API client, wire into app** - `57b8c64` (feat)
   - QueryClient with defaults, query key factory, type-safe API client
   - Wired QueryClientProvider into main.tsx
   - Added queryClient to router context
   - Fixed App.test.tsx for new context shape

2. **Task 2: Create queryOptions factories, API error utilities, route loader integration** - `b2ece7c` (feat)
   - API error parsing utilities
   - queryOptions factories for accounts, transactions, categories
   - Dashboard route loader using ensureQueryData

## Files Created/Modified

**Created:**
- `apps/web/src/lib/query-client.ts` - QueryClient with configured defaults (staleTime, gcTime, retry)
- `apps/web/src/lib/query-keys.ts` - Hierarchical query key factory (accounts, transactions, categories, payees)
- `apps/web/src/lib/api-client.ts` - Type-safe API wrapper using generated OpenAPI types
- `apps/web/src/lib/query-options.ts` - queryOptions factories for all entity types
- `apps/web/src/lib/api-error.ts` - parseApiError, getErrorMessage utilities

**Modified:**
- `apps/web/src/main.tsx` - Added QueryClientProvider wrapper, ReactQueryDevtools
- `apps/web/src/routes.tsx` - Added queryClient to router context, loader on dashboard route
- `apps/web/src/app/App.test.tsx` - Updated test routers to include queryClient

## Decisions Made

1. **QueryClient stale times:** Per-entity configuration based on change frequency:
   - Accounts: 60s (change infrequently)
   - Transactions: 15s (more frequent updates)
   - Categories: 5min (mostly static)
   - Default: 30s (reasonable middle ground)

2. **Provider hierarchy:** QueryClientProvider wraps AuthProvider so auth context can use queries if needed in the future (though auth stays React Context for now)

3. **Auth context unchanged:** Preserved React Context for auth state. TanStack Query is for server state only. This separation is intentional and follows best practices.

4. **API client design:** Functions unwrap AxiosResponse.data to return just the payload. Cleaner signatures for query functions.

5. **Route loader pattern:** Use ensureQueryData (not prefetchQuery) in loaders. Returns cached data if fresh, fetches if stale. Enables instant navigation.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All quality checks passed on first attempt (typecheck, test, lint).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Infrastructure complete for all future UI phases (15-26):**

- ✅ Type-safe API client ready for component use
- ✅ Query key factory supports cache invalidation patterns
- ✅ queryOptions factories ready for useQuery and loaders
- ✅ Error parsing handles FastAPI formats consistently
- ✅ Route loader pattern demonstrated and working
- ✅ ReactQueryDevtools available for debugging

**Next phases (Account List UI, Transaction List UI, Category UI) can immediately:**
- Import and use queryOptions in components via useQuery
- Use ensureQueryData in route loaders for instant navigation
- Import API client functions for mutations
- Use parseApiError for error display

**No blockers.** All infrastructure pieces in place for data-driven UI development.

---
*Phase: 14-frontend-api-routing*
*Completed: 2026-02-11*
