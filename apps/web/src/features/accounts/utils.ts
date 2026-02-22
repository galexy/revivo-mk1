/**
 * Account feature utility functions.
 */
import type { AccountResponse } from '@/lib/api-client';
import type { AccountCategory, AccountGroup } from './types';

/**
 * Mapping of account categories to their labels and account types.
 */
export const ACCOUNT_CATEGORIES: Record<
  AccountCategory,
  { label: string; types: Array<AccountResponse['account_type']> }
> = {
  cash: {
    label: 'Cash',
    types: ['checking', 'savings'],
  },
  credit: {
    label: 'Credit',
    types: ['credit_card'],
  },
  loans: {
    label: 'Loans',
    types: ['loan'],
  },
  investments: {
    label: 'Investments',
    types: ['brokerage', 'ira'],
  },
  rewards: {
    label: 'Rewards',
    types: ['rewards'],
  },
};

/**
 * Groups accounts by category and computes subtotals.
 * Filters out empty groups (categories with no accounts).
 */
export function groupAccounts(accounts: AccountResponse[]): AccountGroup[] {
  return Object.entries(ACCOUNT_CATEGORIES)
    .map(([category, config]) => {
      const categoryAccounts = accounts.filter((account) =>
        config.types.includes(account.account_type),
      );

      const subtotal = categoryAccounts.reduce((sum, account) => {
        return sum + parseFloat(account.current_balance.amount);
      }, 0);

      return {
        category: category as AccountCategory,
        label: config.label,
        accounts: categoryAccounts,
        subtotal,
      };
    })
    .filter((group) => group.accounts.length > 0);
}

/**
 * Formats a number as USD currency.
 * @param amount - Number or string to format
 * @returns Formatted currency string (e.g., "$1,234.56")
 */
export function formatCurrency(amount: string | number): string {
  const numericAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(numericAmount);
}
