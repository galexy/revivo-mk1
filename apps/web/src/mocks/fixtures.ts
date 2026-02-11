/**
 * Test fixtures matching API response shapes.
 * Uses generated types for type safety.
 */
import type {
  AccountResponse,
  AccountListResponse,
  CategoryResponse,
  CategoryListResponse,
  CategoryTreeResponse,
} from '../lib/api-client';

// Mock account fixture
export const mockAccount: AccountResponse = {
  id: 'acc_01234567890',
  user_id: 'usr_01234567890',
  name: 'Test Checking Account',
  account_type: 'checking',
  status: 'active',
  opening_balance: {
    amount: '1000.00',
    currency: 'USD',
  },
  current_balance: {
    amount: '1500.00',
    currency: 'USD',
  },
  opening_date: '2024-01-01T00:00:00Z',
  subtype: null,
  credit_limit: null,
  available_credit: null,
  apr: null,
  term_months: null,
  due_date: null,
  rewards_balance: null,
  institution: {
    name: 'Test Bank',
    website: 'https://testbank.com',
  },
  account_number_last4: '1234',
  closing_date: null,
  notes: 'Test account for unit tests',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
};

// Mock accounts list
export const mockAccountsList: AccountListResponse = {
  accounts: [
    mockAccount,
    {
      ...mockAccount,
      id: 'acc_98765432100',
      name: 'Savings Account',
      account_type: 'savings',
      opening_balance: {
        amount: '5000.00',
        currency: 'USD',
      },
      current_balance: {
        amount: '5250.00',
        currency: 'USD',
      },
    },
  ],
  total: 2,
};

// Mock category fixture
export const mockCategory: CategoryResponse = {
  id: 'cat_01234567890',
  user_id: 'usr_01234567890',
  name: 'Groceries',
  parent_id: null,
  category_type: 'expense',
  is_system: false,
  is_hidden: false,
  sort_order: 1,
  icon: '🛒',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Mock categories list
export const mockCategoriesList: CategoryListResponse = {
  categories: [
    mockCategory,
    {
      ...mockCategory,
      id: 'cat_98765432100',
      name: 'Utilities',
      icon: '⚡',
      sort_order: 2,
    },
  ],
  total: 2,
};

// Mock category tree
export const mockCategoryTree: CategoryTreeResponse = {
  root: [mockCategory],
  children: {},
};

// Auth response fixtures
export const mockTokenResponse = {
  access_token: 'mock_access_token_12345',
  token_type: 'bearer',
};

export const mockUserProfile = {
  id: 'usr_01234567890',
  email: 'test@example.com',
  display_name: 'Test User',
  email_verified: true,
  household: {
    id: 'hh_01234567890',
    name: "Test User's Household",
    is_owner: true,
  },
  created_at: '2024-01-01T00:00:00Z',
};
