/**
 * TanStack Query mutation hook for deleting accounts.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { deleteAccount } from '@/lib/api-client';

export function useDeleteAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (accountId: string): Promise<void> => {
      return deleteAccount(accountId);
    },
    onSettled: (data, error, accountId) => {
      // Invalidate accounts list
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
      // Remove the specific account detail query from cache
      queryClient.removeQueries({ queryKey: queryKeys.accounts.detail(accountId) });
    },
  });
}
