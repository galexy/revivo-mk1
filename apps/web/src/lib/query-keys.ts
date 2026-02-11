/**
 * Query key factory following TkDodo's v5 hierarchical pattern.
 *
 * Structure enables smart cache invalidation:
 * - Invalidate `queryKeys.accounts.all` → invalidates all account queries
 * - Invalidate `queryKeys.accounts.lists()` → invalidates all account lists
 * - Invalidate `queryKeys.accounts.detail(id)` → invalidates single account
 *
 * Pattern: [entity, scope, ...params]
 *
 * @see https://tkdodo.eu/blog/effective-react-query-keys
 */

// Placeholder filter types - Phase 15+ will add real filters
export interface AccountFilters {
  status?: string;
  type?: string;
}

export interface TransactionFilters {
  accountId?: string;
  categoryId?: string;
  startDate?: string;
  endDate?: string;
}

export const queryKeys = {
  accounts: {
    all: ['accounts'] as const,
    lists: () => [...queryKeys.accounts.all, 'list'] as const,
    list: (filters?: AccountFilters) => [...queryKeys.accounts.lists(), filters] as const,
    details: () => [...queryKeys.accounts.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.accounts.details(), id] as const,
  },
  transactions: {
    all: ['transactions'] as const,
    lists: () => [...queryKeys.transactions.all, 'list'] as const,
    list: (filters?: TransactionFilters) => [...queryKeys.transactions.lists(), filters] as const,
    details: () => [...queryKeys.transactions.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.transactions.details(), id] as const,
  },
  categories: {
    all: ['categories'] as const,
    tree: () => [...queryKeys.categories.all, 'tree'] as const,
    lists: () => [...queryKeys.categories.all, 'list'] as const,
  },
  payees: {
    all: ['payees'] as const,
    lists: () => [...queryKeys.payees.all, 'list'] as const,
  },
  user: {
    profile: ['user', 'profile'] as const,
  },
};
