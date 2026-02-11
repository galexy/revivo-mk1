import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCreateAccount } from '../useCreateAccount';
import * as apiClient from '@/lib/api-client';
import type { AccountFormData } from '../../validation/accountSchemas';

// Mock the api-client module
vi.mock('@/lib/api-client', async () => {
  const actual = await vi.importActual('@/lib/api-client');
  return {
    ...actual,
    createCheckingAccount: vi.fn(),
    createSavingsAccount: vi.fn(),
    createCreditCardAccount: vi.fn(),
    createLoanAccount: vi.fn(),
    createBrokerageAccount: vi.fn(),
    createIraAccount: vi.fn(),
    createRewardsAccount: vi.fn(),
  };
});

describe('useCreateAccount', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };

  const mockAccountResponse: apiClient.AccountResponse = {
    id: 'acc_123',
    user_id: 'usr_123',
    name: 'Test Account',
    account_type: 'checking',
    status: 'active',
    opening_balance: { amount: '1000.00', currency: 'USD' },
    current_balance: { amount: '1000.00', currency: 'USD' },
    opening_date: '2024-01-01T00:00:00Z',
    subtype: null,
    credit_limit: null,
    available_credit: null,
    apr: null,
    term_months: null,
    due_date: null,
    rewards_balance: null,
    institution: null,
    account_number_last4: null,
    closing_date: null,
    notes: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  it('calls createCheckingAccount for checking account type', async () => {
    const createCheckingSpy = vi
      .spyOn(apiClient, 'createCheckingAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'checking',
      name: 'My Checking',
      openingBalance: '1000.00',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createCheckingSpy).toHaveBeenCalledWith({
        name: 'My Checking',
        opening_balance: {
          amount: '1000.00',
          currency: 'USD',
        },
      });
    });
  });

  it('calls createSavingsAccount for savings account type', async () => {
    const createSavingsSpy = vi
      .spyOn(apiClient, 'createSavingsAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'savings',
      name: 'My Savings',
      openingBalance: '5000.00',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createSavingsSpy).toHaveBeenCalledWith({
        name: 'My Savings',
        opening_balance: {
          amount: '5000.00',
          currency: 'USD',
        },
      });
    });
  });

  it('calls createCreditCardAccount for credit_card type with credit limit', async () => {
    const createCreditCardSpy = vi
      .spyOn(apiClient, 'createCreditCardAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'credit_card',
      name: 'My Credit Card',
      openingBalance: '0.00',
      creditLimit: '5000.00',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createCreditCardSpy).toHaveBeenCalledWith({
        name: 'My Credit Card',
        opening_balance: {
          amount: '0.00',
          currency: 'USD',
        },
        credit_limit: {
          amount: '5000.00',
          currency: 'USD',
        },
      });
    });
  });

  it('calls createLoanAccount for loan type with apr, term, and subtype', async () => {
    const createLoanSpy = vi
      .spyOn(apiClient, 'createLoanAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'loan',
      name: 'Auto Loan',
      openingBalance: '25000.00',
      apr: '0.0599',
      termMonths: '60',
      subtype: 'auto_loan',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createLoanSpy).toHaveBeenCalledWith({
        name: 'Auto Loan',
        opening_balance: {
          amount: '25000.00',
          currency: 'USD',
        },
        apr: '0.0599',
        term_months: 60,
        subtype: 'auto_loan',
      });
    });
  });

  it('calls createBrokerageAccount for brokerage type', async () => {
    const createBrokerageSpy = vi
      .spyOn(apiClient, 'createBrokerageAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'brokerage',
      name: 'My Brokerage',
      openingBalance: '10000.00',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createBrokerageSpy).toHaveBeenCalledWith({
        name: 'My Brokerage',
        opening_balance: {
          amount: '10000.00',
          currency: 'USD',
        },
      });
    });
  });

  it('calls createIraAccount for ira type with subtype', async () => {
    const createIraSpy = vi
      .spyOn(apiClient, 'createIraAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'ira',
      name: 'Roth IRA',
      openingBalance: '6000.00',
      subtype: 'roth_ira',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createIraSpy).toHaveBeenCalledWith({
        name: 'Roth IRA',
        opening_balance: {
          amount: '6000.00',
          currency: 'USD',
        },
        subtype: 'roth_ira',
      });
    });
  });

  it('calls createRewardsAccount for rewards type with rewards balance', async () => {
    const createRewardsSpy = vi
      .spyOn(apiClient, 'createRewardsAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'rewards',
      name: 'Airline Miles',
      openingBalance: '50000',
      rewardsUnit: 'miles',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createRewardsSpy).toHaveBeenCalledWith({
        name: 'Airline Miles',
        rewards_balance: {
          value: '50000',
          unit: 'miles',
        },
      });
    });
  });

  it('defaults to points for rewards unit if not provided', async () => {
    const createRewardsSpy = vi
      .spyOn(apiClient, 'createRewardsAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'rewards',
      name: 'Cashback',
      openingBalance: '100',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createRewardsSpy).toHaveBeenCalledWith({
        name: 'Cashback',
        rewards_balance: {
          value: '100',
          unit: 'points',
        },
      });
    });
  });

  it('defaults to 0 for credit limit if not provided', async () => {
    const createCreditCardSpy = vi
      .spyOn(apiClient, 'createCreditCardAccount')
      .mockResolvedValue(mockAccountResponse);

    const { result } = renderHook(() => useCreateAccount(), { wrapper });

    const formData: AccountFormData = {
      accountType: 'credit_card',
      name: 'Store Card',
      openingBalance: '0.00',
    };

    result.current.mutate(formData);

    await waitFor(() => {
      expect(createCreditCardSpy).toHaveBeenCalledWith({
        name: 'Store Card',
        opening_balance: {
          amount: '0.00',
          currency: 'USD',
        },
        credit_limit: {
          amount: '0',
          currency: 'USD',
        },
      });
    });
  });
});
