import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AccountSidebar } from '../AccountSidebar';
import type { AccountResponse } from '@/lib/api-client';

// Mock TanStack Router
const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({}),
}));

describe('AccountSidebar', () => {
  const mockOnAddAccount = vi.fn();
  const mockOnEditAccount = vi.fn();
  const mockOnDeleteAccount = vi.fn();

  const mockAccounts: AccountResponse[] = [
    {
      id: 'acc_1',
      user_id: 'usr_1',
      name: 'Checking Account',
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
      name: 'Savings Account',
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
    {
      id: 'acc_3',
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

  const renderSidebar = (accounts = mockAccounts) => {
    return render(
      <AccountSidebar
        accounts={accounts}
        onAddAccount={mockOnAddAccount}
        onEditAccount={mockOnEditAccount}
        onDeleteAccount={mockOnDeleteAccount}
      />,
    );
  };

  it('renders grouped accounts with correct headers', () => {
    renderSidebar();

    // Should show Cash and Credit groups
    expect(screen.getByText('Cash')).toBeInTheDocument();
    expect(screen.getByText('Credit')).toBeInTheDocument();

    // Should show account names
    expect(screen.getByText('Checking Account')).toBeInTheDocument();
    expect(screen.getByText('Savings Account')).toBeInTheDocument();
    expect(screen.getByText('Credit Card')).toBeInTheDocument();
  });

  it('Add Account button calls onAddAccount', async () => {
    renderSidebar();
    const user = userEvent.setup();

    const addButton = screen.getByRole('button', { name: /add account/i });
    await user.click(addButton);

    expect(mockOnAddAccount).toHaveBeenCalled();
  });

  it('renders nothing when empty array is provided', () => {
    const { container } = renderSidebar([]);

    // Should render null (no sidebar)
    expect(container.firstChild).toBeNull();
  });

  it('displays subtotal for each group', () => {
    renderSidebar();

    // Cash group should show combined subtotal (1500 + 5250 = 6750)
    expect(screen.getAllByText('$6,750.00')[0]).toBeInTheDocument();

    // Credit group should show subtotal (-500)
    expect(screen.getAllByText('-$500.00')[0]).toBeInTheDocument();
  });

  it('renders only groups that have accounts', () => {
    renderSidebar();

    // Should have Cash and Credit
    expect(screen.getByText('Cash')).toBeInTheDocument();
    expect(screen.getByText('Credit')).toBeInTheDocument();

    // Should NOT have Loans, Investments, or Rewards (no accounts)
    expect(screen.queryByText('Loans')).not.toBeInTheDocument();
    expect(screen.queryByText('Investments')).not.toBeInTheDocument();
    expect(screen.queryByText('Rewards')).not.toBeInTheDocument();
  });

  it('renders accounts header', () => {
    renderSidebar();

    expect(screen.getByText('Accounts')).toBeInTheDocument();
  });

  it('displays all account types in their correct groups', () => {
    const allTypesAccounts: AccountResponse[] = [
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
        name: 'Loan',
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
        id: 'acc_3',
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
    ];

    renderSidebar(allTypesAccounts);

    // All three groups should appear
    expect(screen.getByText('Cash')).toBeInTheDocument();
    expect(screen.getByText('Loans')).toBeInTheDocument();
    expect(screen.getByText('Investments')).toBeInTheDocument();
  });
});
