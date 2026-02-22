import { describe, it, expect } from 'vitest';
import { groupAccounts, formatCurrency } from './utils';
import type { AccountResponse } from '@/lib/api-client';

describe('groupAccounts', () => {
  it('groups checking and savings accounts under Cash category', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Checking',
        account_type: 'checking',
        status: 'active',
        opening_balance: { amount: '1000.00', currency: 'USD' },
        current_balance: { amount: '1500.00', currency: 'USD' },
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
      },
      {
        id: 'acc_2',
        user_id: 'usr_1',
        name: 'Savings',
        account_type: 'savings',
        status: 'active',
        opening_balance: { amount: '5000.00', currency: 'USD' },
        current_balance: { amount: '5250.00', currency: 'USD' },
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
      },
    ];

    const groups = groupAccounts(accounts);

    expect(groups).toHaveLength(1);
    expect(groups[0].category).toBe('cash');
    expect(groups[0].label).toBe('Cash');
    expect(groups[0].accounts).toHaveLength(2);
    expect(groups[0].subtotal).toBe(6750.0); // 1500 + 5250
  });

  it('groups credit_card under Credit category', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Credit Card',
        account_type: 'credit_card',
        status: 'active',
        opening_balance: { amount: '0.00', currency: 'USD' },
        current_balance: { amount: '-500.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: null,
        credit_limit: { amount: '5000.00', currency: 'USD' },
        available_credit: { amount: '4500.00', currency: 'USD' },
        apr: '0.1899',
        term_months: null,
        due_date: '15',
        rewards_balance: null,
        institution: null,
        account_number_last4: null,
        closing_date: null,
        notes: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    const groups = groupAccounts(accounts);

    expect(groups).toHaveLength(1);
    expect(groups[0].category).toBe('credit');
    expect(groups[0].label).toBe('Credit');
    expect(groups[0].accounts).toHaveLength(1);
    expect(groups[0].subtotal).toBe(-500.0);
  });

  it('groups loan under Loans category', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Auto Loan',
        account_type: 'loan',
        status: 'active',
        opening_balance: { amount: '25000.00', currency: 'USD' },
        current_balance: { amount: '-20000.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: 'auto_loan',
        credit_limit: null,
        available_credit: null,
        apr: '0.0599',
        term_months: 60,
        due_date: null,
        rewards_balance: null,
        institution: null,
        account_number_last4: null,
        closing_date: null,
        notes: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    const groups = groupAccounts(accounts);

    expect(groups).toHaveLength(1);
    expect(groups[0].category).toBe('loans');
    expect(groups[0].label).toBe('Loans');
    expect(groups[0].accounts).toHaveLength(1);
    expect(groups[0].subtotal).toBe(-20000.0);
  });

  it('groups brokerage and ira under Investments category', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Brokerage',
        account_type: 'brokerage',
        status: 'active',
        opening_balance: { amount: '10000.00', currency: 'USD' },
        current_balance: { amount: '12500.00', currency: 'USD' },
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
      },
      {
        id: 'acc_2',
        user_id: 'usr_1',
        name: 'Roth IRA',
        account_type: 'ira',
        status: 'active',
        opening_balance: { amount: '5000.00', currency: 'USD' },
        current_balance: { amount: '6000.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: 'roth_ira',
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
      },
    ];

    const groups = groupAccounts(accounts);

    expect(groups).toHaveLength(1);
    expect(groups[0].category).toBe('investments');
    expect(groups[0].label).toBe('Investments');
    expect(groups[0].accounts).toHaveLength(2);
    expect(groups[0].subtotal).toBe(18500.0); // 12500 + 6000
  });

  it('groups rewards under Rewards category', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Airline Miles',
        account_type: 'rewards',
        status: 'active',
        opening_balance: { amount: '0.00', currency: 'USD' },
        current_balance: { amount: '0.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: null,
        credit_limit: null,
        available_credit: null,
        apr: null,
        term_months: null,
        due_date: null,
        rewards_balance: { value: '50000', unit: 'miles' },
        institution: null,
        account_number_last4: null,
        closing_date: null,
        notes: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    const groups = groupAccounts(accounts);

    expect(groups).toHaveLength(1);
    expect(groups[0].category).toBe('rewards');
    expect(groups[0].label).toBe('Rewards');
    expect(groups[0].accounts).toHaveLength(1);
    expect(groups[0].subtotal).toBe(0.0);
  });

  it('returns empty array when given empty input', () => {
    const groups = groupAccounts([]);
    expect(groups).toEqual([]);
  });

  it('filters out empty groups (categories with no accounts)', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Checking',
        account_type: 'checking',
        status: 'active',
        opening_balance: { amount: '1000.00', currency: 'USD' },
        current_balance: { amount: '1500.00', currency: 'USD' },
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
      },
    ];

    const groups = groupAccounts(accounts);

    // Only cash group should be present, not credit/loans/investments/rewards
    expect(groups).toHaveLength(1);
    expect(groups[0].category).toBe('cash');
  });

  it('correctly calculates subtotal for each group', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Checking',
        account_type: 'checking',
        status: 'active',
        opening_balance: { amount: '1000.00', currency: 'USD' },
        current_balance: { amount: '100.50', currency: 'USD' },
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
      },
      {
        id: 'acc_2',
        user_id: 'usr_1',
        name: 'Savings',
        account_type: 'savings',
        status: 'active',
        opening_balance: { amount: '5000.00', currency: 'USD' },
        current_balance: { amount: '200.75', currency: 'USD' },
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
      },
    ];

    const groups = groupAccounts(accounts);

    expect(groups[0].subtotal).toBe(301.25); // 100.50 + 200.75
  });

  it('handles all 7 account types correctly', () => {
    const accounts: AccountResponse[] = [
      {
        id: 'acc_1',
        user_id: 'usr_1',
        name: 'Checking',
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
      },
      {
        id: 'acc_2',
        user_id: 'usr_1',
        name: 'Savings',
        account_type: 'savings',
        status: 'active',
        opening_balance: { amount: '5000.00', currency: 'USD' },
        current_balance: { amount: '5000.00', currency: 'USD' },
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
      },
      {
        id: 'acc_3',
        user_id: 'usr_1',
        name: 'Credit Card',
        account_type: 'credit_card',
        status: 'active',
        opening_balance: { amount: '0.00', currency: 'USD' },
        current_balance: { amount: '0.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: null,
        credit_limit: { amount: '5000.00', currency: 'USD' },
        available_credit: { amount: '5000.00', currency: 'USD' },
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
      },
      {
        id: 'acc_4',
        user_id: 'usr_1',
        name: 'Auto Loan',
        account_type: 'loan',
        status: 'active',
        opening_balance: { amount: '25000.00', currency: 'USD' },
        current_balance: { amount: '25000.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: 'auto_loan',
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
      },
      {
        id: 'acc_5',
        user_id: 'usr_1',
        name: 'Brokerage',
        account_type: 'brokerage',
        status: 'active',
        opening_balance: { amount: '10000.00', currency: 'USD' },
        current_balance: { amount: '10000.00', currency: 'USD' },
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
      },
      {
        id: 'acc_6',
        user_id: 'usr_1',
        name: 'IRA',
        account_type: 'ira',
        status: 'active',
        opening_balance: { amount: '5000.00', currency: 'USD' },
        current_balance: { amount: '5000.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: 'roth_ira',
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
      },
      {
        id: 'acc_7',
        user_id: 'usr_1',
        name: 'Rewards',
        account_type: 'rewards',
        status: 'active',
        opening_balance: { amount: '0.00', currency: 'USD' },
        current_balance: { amount: '0.00', currency: 'USD' },
        opening_date: '2024-01-01T00:00:00Z',
        subtype: null,
        credit_limit: null,
        available_credit: null,
        apr: null,
        term_months: null,
        due_date: null,
        rewards_balance: { value: '50000', unit: 'miles' },
        institution: null,
        account_number_last4: null,
        closing_date: null,
        notes: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    const groups = groupAccounts(accounts);

    // All 5 categories should have accounts
    expect(groups).toHaveLength(5);
    expect(groups.map((g) => g.category)).toEqual([
      'cash',
      'credit',
      'loans',
      'investments',
      'rewards',
    ]);
    expect(groups[0].accounts).toHaveLength(2); // checking + savings
    expect(groups[1].accounts).toHaveLength(1); // credit_card
    expect(groups[2].accounts).toHaveLength(1); // loan
    expect(groups[3].accounts).toHaveLength(2); // brokerage + ira
    expect(groups[4].accounts).toHaveLength(1); // rewards
  });
});

describe('formatCurrency', () => {
  it('formats positive number with thousands separator', () => {
    expect(formatCurrency('1234.56')).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency('0')).toBe('$0.00');
  });

  it('formats negative number', () => {
    expect(formatCurrency('-542.30')).toBe('-$542.30');
  });

  it('formats large number', () => {
    expect(formatCurrency('1000000')).toBe('$1,000,000.00');
  });

  it('handles numeric input', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('handles whole numbers with decimal places', () => {
    expect(formatCurrency('100')).toBe('$100.00');
  });

  it('handles very small numbers', () => {
    expect(formatCurrency('0.01')).toBe('$0.01');
  });
});
