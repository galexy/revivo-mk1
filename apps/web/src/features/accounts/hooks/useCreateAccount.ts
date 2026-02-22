/**
 * TanStack Query mutation hook for creating accounts.
 * Maps wizard form data to type-specific API request shapes.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  createCheckingAccount,
  createSavingsAccount,
  createCreditCardAccount,
  createLoanAccount,
  createBrokerageAccount,
  createIraAccount,
  createRewardsAccount,
  type AccountResponse,
  type CreateCheckingAccountRequest,
  type CreateSavingsAccountRequest,
  type CreateCreditCardAccountRequest,
  type CreateLoanAccountRequest,
  type CreateBrokerageAccountRequest,
  type CreateIraAccountRequest,
  type CreateRewardsAccountRequest,
} from '@/lib/api-client';
import type { AccountFormData } from '../validation/accountSchemas';

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formData: AccountFormData): Promise<AccountResponse> => {
      const { accountType, name, openingBalance } = formData;

      // Common fields for most account types
      const commonData = {
        name,
        opening_balance: {
          amount: openingBalance, // API accepts number | string
          currency: 'USD',
        },
      };

      // Map accountType to the correct API function
      switch (accountType) {
        case 'checking': {
          const data: CreateCheckingAccountRequest = commonData;
          return createCheckingAccount(data);
        }
        case 'savings': {
          const data: CreateSavingsAccountRequest = commonData;
          return createSavingsAccount(data);
        }
        case 'credit_card': {
          const data: CreateCreditCardAccountRequest = {
            name,
            opening_balance: commonData.opening_balance,
            credit_limit: {
              amount: formData.creditLimit || '0',
              currency: 'USD',
            },
          };
          return createCreditCardAccount(data);
        }
        case 'loan': {
          // Convert APR from percentage (user input) to decimal (API expects)
          const aprDecimal = formData.apr ? (parseFloat(formData.apr) / 100).toString() : '0';
          const data: CreateLoanAccountRequest = {
            name,
            opening_balance: commonData.opening_balance,
            apr: aprDecimal,
            term_months: parseInt(formData.termMonths || '0', 10),
            subtype: formData.subtype as
              | 'mortgage'
              | 'auto_loan'
              | 'personal_loan'
              | 'line_of_credit',
          };
          return createLoanAccount(data);
        }
        case 'brokerage': {
          const data: CreateBrokerageAccountRequest = commonData;
          return createBrokerageAccount(data);
        }
        case 'ira': {
          const data: CreateIraAccountRequest = {
            name,
            opening_balance: commonData.opening_balance,
            subtype: formData.subtype as 'traditional_ira' | 'roth_ira' | 'sep_ira',
          };
          return createIraAccount(data);
        }
        case 'rewards': {
          const data: CreateRewardsAccountRequest = {
            name,
            rewards_balance: {
              value: openingBalance, // API accepts number | string
              unit: formData.rewardsUnit || 'points',
            },
          };
          return createRewardsAccount(data);
        }
        default:
          throw new Error(`Unsupported account type: ${accountType}`);
      }
    },
    onSettled: () => {
      // Invalidate accounts list to refetch after create
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts.lists() });
    },
  });
}
