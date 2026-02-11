/**
 * queryOptions factories for TanStack Query.
 *
 * These factories define query keys, query functions, and per-entity stale times.
 * Used by route loaders (ensureQueryData) and components (useQuery).
 *
 * Pattern: Define queryOptions once, use everywhere for consistency.
 */
import { queryOptions } from '@tanstack/react-query';
import { queryKeys } from './query-keys';
import type { TransactionFilters } from './query-keys';
import {
  fetchAccounts,
  fetchAccount,
  fetchTransactions,
  fetchTransaction,
  fetchCategories,
  fetchCategoryTree,
} from './api-client';

// Accounts
export const accountsQueryOptions = queryOptions({
  queryKey: queryKeys.accounts.lists(),
  queryFn: fetchAccounts,
  staleTime: 60_000, // 1 minute - accounts change infrequently
});

export const accountDetailQueryOptions = (id: string) =>
  queryOptions({
    queryKey: queryKeys.accounts.detail(id),
    queryFn: () => fetchAccount(id),
    staleTime: 60_000, // 1 minute
  });

// Transactions
export const transactionsQueryOptions = (filters?: TransactionFilters) =>
  queryOptions({
    queryKey: queryKeys.transactions.list(filters),
    queryFn: () => fetchTransactions(filters?.accountId),
    staleTime: 15_000, // 15 seconds - transactions change more frequently
  });

export const transactionDetailQueryOptions = (id: string) =>
  queryOptions({
    queryKey: queryKeys.transactions.detail(id),
    queryFn: () => fetchTransaction(id),
    staleTime: 15_000, // 15 seconds
  });

// Categories
export const categoriesQueryOptions = queryOptions({
  queryKey: queryKeys.categories.lists(),
  queryFn: fetchCategories,
  staleTime: 5 * 60_000, // 5 minutes - categories are mostly static
});

export const categoryTreeQueryOptions = queryOptions({
  queryKey: queryKeys.categories.tree(),
  queryFn: fetchCategoryTree,
  staleTime: 5 * 60_000, // 5 minutes
});

// Payees - Placeholder for Phase 15+
// export const payeesQueryOptions = queryOptions({
//   queryKey: queryKeys.payees.lists(),
//   queryFn: fetchPayees,
//   staleTime: 60_000, // 1 minute
// });
