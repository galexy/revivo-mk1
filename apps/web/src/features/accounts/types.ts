/**
 * Account feature types and interfaces.
 */
import type { AccountResponse } from '@/lib/api-client';

/**
 * Account category used for grouping accounts in the sidebar.
 */
export type AccountCategory = 'cash' | 'credit' | 'loans' | 'investments' | 'rewards';

/**
 * Grouped accounts by category with computed subtotal.
 */
export interface AccountGroup {
  category: AccountCategory;
  label: string;
  accounts: AccountResponse[];
  subtotal: number;
}
