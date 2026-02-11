/**
 * TanStack Query mutation hook for updating accounts.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { updateAccount, type AccountResponse, type UpdateAccountRequest } from '@/lib/api-client';

interface UpdateAccountParams {
  id: string;
  data: UpdateAccountRequest;
}

export function useUpdateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: UpdateAccountParams): Promise<AccountResponse> => {
      return updateAccount(id, data);
    },
    onSettled: (data, error, variables) => {
      // Invalidate accounts list and the specific account detail
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.detail(variables.id) });
    },
  });
}
