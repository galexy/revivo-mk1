# Phase 14: Frontend API & Routing - Research

**Researched:** 2026-02-11
**Domain:** React server state management, OpenAPI TypeScript code generation, TanStack Query + TanStack Router integration
**Confidence:** HIGH

## Summary

Phase 14 establishes the data layer that all future UI phases (15-26) will build upon. The standard approach is TanStack Query v5 for server state management with openapi-typescript for type-safe API client generation. TanStack Router (already configured in Phase 13) integrates with TanStack Query via route loaders for instant navigation. The established pattern follows TkDodo's recommendations: queryOptions API for type-safe reusable queries, query key hierarchies for smart invalidation, and optimistic updates for inline edits.

The codebase already has Axios interceptors handling auth token injection and refresh (Phase 13), so all query functions will use the existing `api` instance. OpenAPI spec is available at `/openapi.json` from the FastAPI backend. shadcn/ui includes Sonner for toast notifications (already available in libs/ui).

**Primary recommendation:** Use openapi-typescript (not orval or openapi-generator) to generate TypeScript types from `/openapi.json`, then wrap the existing Axios instance with type-safe helpers. TanStack Query with queryOptions API provides type inference and reusability. Route loaders use `ensureQueryData()` for prefetching before navigation.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-query | ^5.x | Server state management | Industry standard for React server state, 50M+ downloads/month, maintained by TanStack team |
| openapi-typescript | ^7.x | TypeScript type generation from OpenAPI | Most popular OpenAPI type generator (1.7M weekly downloads), type-only output (no runtime), works with any HTTP client |
| @tanstack/react-query-devtools | ^5.x | Query debugging tools | Official devtools for inspecting queries, mutations, cache state |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sonner | (via shadcn/ui) | Toast notifications | Already included in libs/ui from Phase 12, modern React 19 compatible |
| axios | ^1.x (existing) | HTTP client | Already configured with auth interceptors in Phase 13 |
| zod | ^4.x (existing) | Client-side validation | Already used for form validation, can validate API responses |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openapi-typescript | orval | Orval generates runtime code (React Query hooks), less flexible, worse IDE performance due to type inference complexity |
| openapi-typescript | openapi-generator | Generates full SDK with runtime, larger bundle, less control over HTTP client |
| TanStack Query | SWR | SWR is simpler but lacks mutations, optimistic updates, prefetching, and devtools |
| axios | openapi-fetch | openapi-fetch is fetch-based (6kb), but project already has Axios with auth interceptors |

**Installation:**
```bash
# In apps/web/
pnpm add @tanstack/react-query @tanstack/react-query-devtools
pnpm add -D openapi-typescript
```

## Architecture Patterns

### Recommended Project Structure
```
apps/web/src/
├── lib/
│   ├── api.ts              # Existing Axios instance with auth interceptors
│   ├── api-types.ts        # Generated TypeScript types from OpenAPI spec
│   └── query-client.ts     # QueryClient configuration
├── queries/
│   ├── accounts.ts         # Query options for accounts API
│   ├── transactions.ts     # Query options for transactions API
│   └── users.ts            # Query options for user/profile API
├── features/
│   └── [feature]/
│       ├── components/     # UI components
│       └── hooks/          # Feature-specific query hooks (optional)
└── routes.tsx              # TanStack Router routes with loaders
```

### Pattern 1: Query Options API (TkDodo v5 Pattern)
**What:** Co-locate queryKey and queryFn in reusable queryOptions objects for type-safe queries
**When to use:** All queries (preferred over inline useQuery)
**Example:**
```typescript
// Source: https://tkdodo.eu/blog/the-query-options-api
// queries/accounts.ts
import { queryOptions } from '@tanstack/react-query';
import api from '../lib/api';
import type { Account } from '../lib/api-types';

export const accountsQueries = {
  // Query key hierarchy base
  all: () => ['accounts'] as const,
  lists: () => [...accountsQueries.all(), 'list'] as const,
  list: (filters?: { type?: string }) =>
    queryOptions({
      queryKey: [...accountsQueries.lists(), filters] as const,
      queryFn: async () => {
        const { data } = await api.get<Account[]>('/accounts', { params: filters });
        return data;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes - accounts don't change often
    }),
  details: () => [...accountsQueries.all(), 'detail'] as const,
  detail: (id: string) =>
    queryOptions({
      queryKey: [...accountsQueries.details(), id] as const,
      queryFn: async () => {
        const { data } = await api.get<Account>(`/accounts/${id}`);
        return data;
      },
      staleTime: 5 * 60 * 1000,
    }),
};

// In components:
function AccountList() {
  const { data: accounts } = useQuery(accountsQueries.list());
  // ...
}

// In route loaders:
const accountsRoute = createRoute({
  loader: ({ context }) => {
    context.queryClient.ensureQueryData(accountsQueries.list());
  },
});
```

### Pattern 2: Route Loader Prefetching
**What:** Use TanStack Router loaders to prefetch data before navigation
**When to use:** All data-heavy routes for instant navigation feel
**Example:**
```typescript
// Source: https://tanstack.com/router/latest/docs/integrations/query
import { createRoute } from '@tanstack/react-router';
import { accountsQueries } from '../queries/accounts';

const accountDetailRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: '/accounts/$accountId',
  loader: ({ context, params }) => {
    // ensureQueryData returns cached data immediately if fresh, fetches if stale
    // This runs BEFORE component renders, so navigation feels instant
    return context.queryClient.ensureQueryData(
      accountsQueries.detail(params.accountId)
    );
  },
  component: AccountDetailPage,
});
```

### Pattern 3: Optimistic Updates with Rollback
**What:** Update UI immediately, rollback if mutation fails
**When to use:** Inline edits (transaction fields), low-cost actions
**Example:**
```typescript
// Source: https://tanstack.com/query/latest/docs/react/guides/optimistic-updates
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { transactionsQueries } from '../queries/transactions';

function useUpdateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (update: { id: string; amount: number }) => {
      const { data } = await api.patch(`/transactions/${update.id}`, update);
      return data;
    },
    onMutate: async (update) => {
      // Cancel outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: transactionsQueries.all() });

      // Snapshot the previous value
      const previousTransactions = queryClient.getQueryData(
        transactionsQueries.list()
      );

      // Optimistically update to the new value
      queryClient.setQueryData(transactionsQueries.list(), (old) =>
        old?.map((txn) =>
          txn.id === update.id ? { ...txn, ...update } : txn
        )
      );

      // Return context with the snapshotted value
      return { previousTransactions };
    },
    onError: (err, update, context) => {
      // Rollback to the previous value
      if (context?.previousTransactions) {
        queryClient.setQueryData(
          transactionsQueries.list(),
          context.previousTransactions
        );
      }
    },
    onSettled: () => {
      // Always refetch after error or success to ensure consistency
      queryClient.invalidateQueries({ queryKey: transactionsQueries.all() });
    },
  });
}
```

### Pattern 4: Error Handling with Context
**What:** Handle 4xx errors locally, propagate 5xx to error boundary
**When to use:** Forms (show validation errors inline), background refreshes (show toast)
**Example:**
```typescript
// Source: https://tkdodo.eu/blog/react-query-error-handling
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';

function AccountList() {
  const { data, error, isError } = useQuery({
    ...accountsQueries.list(),
    // Don't throw 4xx to error boundary - show inline
    throwOnError: (error) => {
      const status = error.response?.status;
      return status ? status >= 500 : false; // Only throw 5xx
    },
  });

  // Handle 4xx errors inline
  if (isError && error.response?.status < 500) {
    return <div>Failed to load accounts: {error.message}</div>;
  }

  // 5xx errors throw to nearest error boundary
  return <AccountTable accounts={data} />;
}

// For mutations (background operations):
function useDeleteAccount() {
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/accounts/${id}`);
    },
    onError: (error) => {
      // Mutation errors don't throw - handle with toast
      const message = error.response?.status >= 500
        ? 'Server error. Please try again.'
        : error.response?.data?.message || 'Failed to delete account';
      toast.error(message);
    },
    onSuccess: () => {
      toast.success('Account deleted');
    },
  });
}
```

### Pattern 5: OpenAPI TypeScript Type Generation
**What:** Generate TypeScript types from backend OpenAPI spec
**When to use:** Always - keeps frontend types in sync with backend
**Example:**
```typescript
// package.json script:
{
  "scripts": {
    "generate:api-types": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-types.ts"
  }
}

// Generated src/lib/api-types.ts (example):
export interface paths {
  "/accounts": {
    get: {
      responses: {
        200: { content: { "application/json": Account[] } };
      };
    };
    post: {
      requestBody: { content: { "application/json": CreateAccountRequest } };
      responses: {
        201: { content: { "application/json": Account } };
      };
    };
  };
}

// Usage in query functions:
import type { paths } from '../lib/api-types';

type AccountsResponse = paths["/accounts"]["get"]["responses"][200]["content"]["application/json"];

// Or use helper type:
type ApiResponse<T extends keyof paths, M extends keyof paths[T]> =
  paths[T][M]["responses"][200]["content"]["application/json"];

type Accounts = ApiResponse<"/accounts", "get">;
```

### Anti-Patterns to Avoid
- **Don't map query data to Redux/Context:** TanStack Query already shares data between components via cache. Only use Context for true client state (theme, locale)
- **Don't use onSuccess/onError in useQuery:** These encourage side effects in query definitions. Use `useEffect` in components for side effects based on query state
- **Don't mutate query data directly:** Always use `setQueryData` or invalidate queries. Direct mutation breaks reactivity
- **Don't forget query key consistency:** Use query factories (accountsQueries.all(), etc.) to ensure consistent keys for invalidation
- **Don't set staleTime to 0 everywhere:** Default staleTime: 0 means always refetch. Set appropriate staleTime per data type (e.g., 5min for accounts, 1min for transactions)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OpenAPI → TypeScript types | Custom parser, manual type definitions | openapi-typescript | Handles oneOf/anyOf/allOf composition, discriminated unions, nullable fields, enum types, generates 100% accurate types |
| Request deduplication | Custom request queue | TanStack Query (built-in) | Automatically deduplicates concurrent requests with same query key |
| Background refetch on window focus | Custom visibility listener | TanStack Query refetchOnWindowFocus | Handles edge cases (tab visibility API, focus events, mobile browsers) |
| Optimistic update rollback | Manual state snapshots | TanStack Query onMutate/onError context | Type-safe context passing between mutation lifecycle hooks |
| Query invalidation hierarchy | Manual cache clearing | TanStack Query partial key matching | `invalidateQueries({ queryKey: ['accounts'] })` invalidates all account queries |
| Retry logic with exponential backoff | Custom retry loop | TanStack Query retry option | Built-in exponential backoff, configurable per query |
| Stale-while-revalidate | Custom cache + timestamp checks | TanStack Query staleTime + gcTime | Automatic background refetch when data becomes stale |
| Loading/error/success states | Manual useState flags | TanStack Query status | Single source of truth for query lifecycle state |

**Key insight:** TanStack Query handles the hard parts of async state management (race conditions, cache invalidation, concurrent requests, error recovery). openapi-typescript eliminates type drift between frontend and backend (one source of truth: the OpenAPI spec).

## Common Pitfalls

### Pitfall 1: Request Waterfalls from Nested Components
**What goes wrong:** Parent renders → fetches data → child renders → fetches data. Each step blocks the next, creating waterfall.
**Why it happens:** Queries in child components only start after parent renders with its data
**How to avoid:** Use route loaders to prefetch all data in parallel before rendering:
```typescript
loader: ({ context }) => {
  // These run in parallel:
  return Promise.all([
    context.queryClient.ensureQueryData(accountsQueries.list()),
    context.queryClient.ensureQueryData(transactionsQueries.list()),
  ]);
}
```
**Warning signs:** DevTools Network tab shows sequential requests, slow navigation, Lighthouse flags render-blocking requests

### Pitfall 2: Query Key Inconsistency Breaking Invalidation
**What goes wrong:** `invalidateQueries({ queryKey: ['accounts'] })` doesn't invalidate anything
**Why it happens:** Query defined with `queryKey: ['account']` (singular) or in different order
**How to avoid:** Use query factories (single source of truth for keys):
```typescript
// queries/accounts.ts - SINGLE source of truth
export const accountsQueries = {
  all: () => ['accounts'] as const,
  list: () => [...accountsQueries.all(), 'list'] as const,
};

// Always use the factory:
useQuery(accountsQueries.list()); // ✓
useQuery({ queryKey: ['accounts', 'list'] }); // ✗ Don't hardcode
```
**Warning signs:** Data doesn't refresh after mutation, DevTools shows stale data, manual page refresh fixes it

### Pitfall 3: Forgetting to Cancel Queries in Optimistic Updates
**What goes wrong:** Optimistic update gets overwritten by in-flight request that completes after
**Why it happens:** Background refetch completes after optimistic update, restoring old data
**How to avoid:** Always `cancelQueries()` in `onMutate`:
```typescript
onMutate: async (update) => {
  // CRITICAL: Cancel any outgoing refetches
  await queryClient.cancelQueries({ queryKey: transactionsQueries.all() });
  // Now safe to optimistically update
  queryClient.setQueryData(...);
}
```
**Warning signs:** Optimistic update briefly shows then reverts, data flickers

### Pitfall 4: Setting staleTime Too Low (Performance)
**What goes wrong:** Every component mount triggers refetch, unnecessary network requests
**Why it happens:** Default staleTime: 0 means data is immediately stale, refetches on every mount
**How to avoid:** Set staleTime based on data mutability:
```typescript
// Rarely changes - set high staleTime
accountsQueries.list() → staleTime: 5 * 60 * 1000 (5 min)

// Changes frequently - set low staleTime
transactionsQueries.list() → staleTime: 60 * 1000 (1 min)

// Real-time data - keep default (0)
dashboardQueries.summary() → staleTime: 0
```
**Warning signs:** DevTools Network tab shows duplicate requests, slow navigation between pages

### Pitfall 5: OpenAPI oneOf/anyOf Type Inference Issues
**What goes wrong:** TypeScript can't discriminate union types from oneOf, requires type narrowing everywhere
**Why it happens:** TypeScript unions don't provide XOR behavior, OpenAPI oneOf is ambiguous
**How to avoid:** Backend should use discriminator field for oneOf:
```yaml
# Backend OpenAPI schema - GOOD:
oneOf:
  - $ref: '#/components/schemas/CheckingAccount'
  - $ref: '#/components/schemas/SavingsAccount'
discriminator:
  propertyName: account_type  # TypeScript can narrow on this

# Frontend usage:
if (account.account_type === 'checking') {
  // TypeScript knows this is CheckingAccount
  account.routing_number; // ✓ Type-safe
}
```
**Warning signs:** Lots of `as` type assertions, TypeScript errors on valid code

### Pitfall 6: TanStack Router beforeLoad Waterfalls
**What goes wrong:** Nested routes with beforeLoad hooks run sequentially (parent → child → grandchild)
**Why it happens:** beforeLoad runs sequentially from outermost to innermost, blocking loader execution
**How to avoid:** Keep beforeLoad lightweight (auth checks only), move data fetching to loaders (run in parallel):
```typescript
beforeLoad: ({ context }) => {
  // ✓ Fast: just check auth state
  if (!context.auth.isAuthenticated) throw redirect({ to: '/login' });
},
loader: ({ context }) => {
  // ✓ Parallel: all route loaders run concurrently
  return context.queryClient.ensureQueryData(accountsQueries.list());
}
```
**Warning signs:** Nested routes slow to load, DevTools shows sequential data fetches

### Pitfall 7: Axios Interceptor + Query Retry Infinite Loop
**What goes wrong:** Query retries 3 times → each retry triggers token refresh → 12 refresh attempts
**Why it happens:** TanStack Query retry multiplies with Axios interceptor retry
**How to avoid:** Disable query retry for auth errors (let interceptor handle):
```typescript
queryClient: new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry auth errors - interceptor handles token refresh
        if (error.response?.status === 401) return false;
        // Retry others up to 3 times
        return failureCount < 3;
      },
    },
  },
});
```
**Warning signs:** DevTools shows multiple concurrent /auth/refresh requests, rate limiting errors

## Code Examples

Verified patterns from official sources:

### QueryClient Configuration
```typescript
// Source: https://tanstack.com/query/v5/docs/react/guides/important-defaults
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // How long data stays fresh (no refetch during this period)
      staleTime: 60 * 1000, // 1 minute default, override per query

      // How long unused data stays in cache before garbage collection
      gcTime: 5 * 60 * 1000, // 5 minutes (default)

      // Refetch when window regains focus (good for stale data)
      refetchOnWindowFocus: true,

      // Refetch on network reconnect
      refetchOnReconnect: true,

      // Retry failed requests
      retry: (failureCount, error) => {
        // Don't retry 4xx errors (client errors)
        if (error.response?.status >= 400 && error.response?.status < 500) {
          return false;
        }
        // Retry 5xx up to 3 times
        return failureCount < 3;
      },
    },
    mutations: {
      // Don't retry mutations by default (user can retry manually)
      retry: false,
    },
  },
});
```

### App Integration with Router Context
```typescript
// Source: https://tanstack.com/router/latest/docs/integrations/query
// src/main.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { RouterProvider } from '@tanstack/react-router';
import { router } from './router';
import { queryClient } from './lib/query-client';
import { useAuth } from './features/auth/context/useAuth';

function App() {
  const auth = useAuth();

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} context={{ auth, queryClient }} />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Query Key Hierarchy with Type Safety
```typescript
// Source: https://tkdodo.eu/blog/effective-react-query-keys
// queries/transactions.ts
import { queryOptions } from '@tanstack/react-query';

export const transactionsQueries = {
  // Base key - invalidate all transactions
  all: () => ['transactions'] as const,

  // List queries - filtered/sorted variations
  lists: () => [...transactionsQueries.all(), 'list'] as const,
  list: (filters?: { accountId?: string; startDate?: string; endDate?: string }) =>
    queryOptions({
      queryKey: [...transactionsQueries.lists(), filters] as const,
      queryFn: async () => {
        const { data } = await api.get('/transactions', { params: filters });
        return data;
      },
      staleTime: 60 * 1000, // 1 minute - transactions change often
    }),

  // Detail queries - individual transactions
  details: () => [...transactionsQueries.all(), 'detail'] as const,
  detail: (id: string) =>
    queryOptions({
      queryKey: [...transactionsQueries.details(), id] as const,
      queryFn: async () => {
        const { data } = await api.get(`/transactions/${id}`);
        return data;
      },
    }),
};

// Invalidation patterns:
queryClient.invalidateQueries({ queryKey: transactionsQueries.all() }); // All
queryClient.invalidateQueries({ queryKey: transactionsQueries.lists() }); // All lists
queryClient.invalidateQueries({
  queryKey: transactionsQueries.list({ accountId: '123' })
}); // Specific list
```

### Mutation with Toast Feedback
```typescript
// Source: https://tanstack.com/query/v5/docs/react/guides/mutations
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAccountRequest) => {
      const response = await api.post('/accounts', data);
      return response.data;
    },
    onSuccess: (newAccount) => {
      // Invalidate all account lists to trigger refetch
      queryClient.invalidateQueries({ queryKey: accountsQueries.all() });

      // Optimistically add to cache (optional - shows immediately without refetch)
      queryClient.setQueryData(
        accountsQueries.detail(newAccount.id),
        newAccount
      );

      toast.success('Account created');
    },
    onError: (error) => {
      const message = error.response?.status >= 500
        ? 'Server error. Please try again.'
        : error.response?.data?.message || 'Failed to create account';
      toast.error(message);
    },
  });
}

// Usage in component:
function CreateAccountForm() {
  const createAccount = useCreateAccount();
  const navigate = useNavigate();

  const onSubmit = async (data: CreateAccountRequest) => {
    const account = await createAccount.mutateAsync(data);
    // Navigate after success
    navigate({ to: `/accounts/${account.id}` });
  };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| useErrorBoundary flag | throwOnError function | TanStack Query v5 (2023) | More control: can throw only 5xx, handle 4xx locally |
| cacheTime | gcTime | TanStack Query v5 (2023) | Clearer naming (garbage collection time) |
| Query key factory functions | queryOptions API | TanStack Query v5 (2023) | Type-safe query definitions, better DX, single source of truth |
| Manual query hooks | Route loaders + ensureQueryData | TanStack Router v1 (2024) | Prefetch before navigation, instant page transitions |
| orval (generate hooks) | openapi-typescript (types only) | Trend shift 2024-2025 | More flexible, better IDE performance, works with any client |
| react-toastify | sonner | 2024-2025 | React 19 compatible, better animations, smaller bundle |

**Deprecated/outdated:**
- **cacheTime:** Renamed to gcTime in v5. Still works but deprecated
- **useErrorBoundary:** Renamed to throwOnError in v5. Old name still works but deprecated
- **onSuccess/onError in useQuery:** Removed in v5. Use useEffect instead for component-level side effects
- **setLogger:** Removed in v5. No longer needed with improved error handling

## Open Questions

Things that couldn't be fully resolved:

1. **OpenAPI spec access in CI/CD**
   - What we know: Backend serves spec at `/openapi.json`, needs running API
   - What's unclear: How to generate types in CI without starting backend (chicken-egg problem)
   - Recommendation: Add `generate:api-types` as manual script, document in CLAUDE.md. Future: export static OpenAPI file from backend for CI

2. **Skeleton loader implementation**
   - What we know: shadcn/ui doesn't include skeleton component yet (needs CLI generation)
   - What's unclear: Whether Phase 14 should add skeleton or defer to Phase 15 (first data-heavy UI)
   - Recommendation: Defer to Phase 15. Phase 14 establishes patterns, Phase 15 implements first real data views

3. **Background refresh visual indicator**
   - What we know: User wants subtle connection state indicator (like Slack yellow banner)
   - What's unclear: Where to place (header? status bar?), what triggers "disconnected" state
   - Recommendation: Defer to Phase 16/17 when header/layout are built. Phase 14 adds isFetching state, UI phase consumes it

4. **Pull-to-refresh mobile pattern**
   - What we know: User wants pull-to-refresh on mobile, refresh button on desktop
   - What's unclear: Which library (react-simple-pull-to-refresh? custom?), conflicts with scroll
   - Recommendation: Defer to first mobile-optimized phase. Desktop refresh button is sufficient for Phase 14

## Sources

### Primary (HIGH confidence)
- [TanStack Query Official Docs](https://tanstack.com/query/latest/docs/framework/react/guides/queries) - Core concepts, API reference
- [TanStack Router Query Integration](https://tanstack.com/router/latest/docs/integrations/query) - Official integration guide
- [TkDodo's Blog - Practical React Query](https://tkdodo.eu/blog/practical-react-query) - Maintainer best practices
- [TkDodo's Blog - Query Options API](https://tkdodo.eu/blog/the-query-options-api) - v5 patterns
- [TkDodo's Blog - React Query Error Handling](https://tkdodo.eu/blog/react-query-error-handling) - Error strategies
- [TanStack Query Optimistic Updates](https://tanstack.com/query/latest/docs/react/guides/optimistic-updates) - Official pattern
- [openapi-typescript Documentation](https://openapi-ts.dev/examples) - Type generation
- [shadcn/ui Sonner Component](https://ui.shadcn.com/docs/components/radix/sonner) - Toast library
- [Playwright Authentication Guide](https://playwright.dev/docs/auth) - Auth fixtures

### Secondary (MEDIUM confidence)
- [TanStack Query Important Defaults](https://tanstack.com/query/v5/docs/react/guides/important-defaults) - staleTime/gcTime guidance (verified with TkDodo blog)
- [OpenAPI TypeScript Advanced Guide](https://openapi-ts.dev/6.x/advanced) - oneOf/anyOf handling
- [Frontend Masters TanStack Router Data Loading](https://frontendmasters.com/blog/tanstack-router-data-loading-2/) - Route loader patterns
- [BrowserStack Playwright Fixtures Guide](https://www.browserstack.com/guide/fixtures-in-playwright) - Fixture patterns
- [npm trends: openapi-typescript vs orval](https://npmtrends.com/openapi-typescript-vs-orval-vs-swagger-typescript-api-generator) - Library comparison

### Tertiary (LOW confidence - flagged for validation)
- [Medium: Common TanStack Query Mistakes](https://www.buncolak.com/posts/avoiding-common-mistakes-with-tanstack-query-part-1/) - Community pitfalls (not official)
- [Knock.app React Notification Libraries](https://knock.app/blog/the-top-notification-libraries-for-react) - Sonner popularity claim
- [react-loading-skeleton](https://www.npmjs.com/package/react-loading-skeleton) - Skeleton loader option

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - TanStack Query is industry standard (50M+ downloads/month), openapi-typescript most popular type generator (1.7M/week), official TanStack Router integration documented
- Architecture: HIGH - Patterns from TkDodo (TanStack Query maintainer) and official TanStack Router docs, verified with existing codebase (Axios + auth interceptors already configured)
- Pitfalls: MEDIUM-HIGH - Request waterfalls and query key consistency from official docs (HIGH), optimistic update cancellation from community + official docs (MEDIUM), Axios + retry infinite loop from general knowledge (MEDIUM, needs validation)
- Code examples: HIGH - All examples from official TanStack docs or TkDodo blog (maintainer)

**Research date:** 2026-02-11
**Valid until:** 2026-03-13 (30 days - TanStack Query is stable, v5 released 2023)
