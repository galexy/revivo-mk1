/**
 * Convenience hook for fetching accounts list.
 * Thin wrapper around useQuery with accountsQueryOptions.
 */
import { useQuery } from '@tanstack/react-query';
import { accountsQueryOptions } from '@/lib/query-options';

export function useAccounts() {
  const query = useQuery(accountsQueryOptions);

  return {
    accounts: query.data?.accounts ?? [],
    isLoading: query.isLoading,
    error: query.error,
  };
}
