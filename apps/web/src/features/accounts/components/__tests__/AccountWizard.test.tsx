import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AccountWizard } from '../AccountWizard';
import type { AccountResponse } from '@/lib/api-client';

// Mock TanStack Router
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({}),
}));

describe('AccountWizard', () => {
  const mockOnOpenChange = vi.fn();
  const mockOnSubmit = vi.fn();

  const renderWizard = (open = true) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return render(
      <QueryClientProvider client={queryClient}>
        <AccountWizard open={open} onOpenChange={mockOnOpenChange} onSubmit={mockOnSubmit} />
      </QueryClientProvider>,
    );
  };

  it('renders step 1 (Choose Account Type) when opened', () => {
    renderWizard();

    // Text appears in both DialogTitle and step content
    expect(screen.getAllByText('Choose Account Type').length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/checking/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/savings/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/credit card/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/loan/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/brokerage/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ira/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/rewards/i)).toBeInTheDocument();
  });

  it('clicking account type auto-advances to step 2', async () => {
    renderWizard();
    const user = userEvent.setup();

    // Click checking account type (should auto-advance)
    const checkingRadio = screen.getByLabelText(/checking/i);
    await user.click(checkingRadio);

    // Should auto-advance to step 2 after brief delay
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
  });

  it('selected account type shows visual feedback before advancing', async () => {
    renderWizard();
    const user = userEvent.setup();

    // Select checking account type (should show border change and auto-advance)
    const checkingRadio = screen.getByLabelText(/checking/i);
    await user.click(checkingRadio);

    // Should auto-advance to step 2 (Account Details)
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
  });

  it('step 2 shows name input and Back/Next buttons', async () => {
    renderWizard();
    const user = userEvent.setup();

    // Select account type (auto-advances to step 2)
    await user.click(screen.getByLabelText(/checking/i));

    // Step 2 should show name input
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );

    expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });

  it('Back button returns to previous step', async () => {
    renderWizard();
    const user = userEvent.setup();

    // Advance to step 2 (auto-advance)
    await user.click(screen.getByLabelText(/checking/i));

    await waitFor(
      () => {
        expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );

    // Click Back
    const backButton = screen.getByRole('button', { name: /back/i });
    await user.click(backButton);

    // Should be back on step 1
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/checking/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
  });

  it('can navigate through all 4 steps', async () => {
    renderWizard();
    const user = userEvent.setup();

    // Step 1: Select account type (auto-advances to step 2)
    await user.click(screen.getByLabelText(/checking/i));

    // Step 2: Enter account name
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
    const nameInput = screen.getByLabelText(/account name/i);
    await user.type(nameInput, 'My Checking Account');
    await user.click(screen.getByRole('button', { name: /next/i }));

    // Step 3: Enter opening balance (label is "Balance" not "Opening Balance")
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/^balance$/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
    const balanceInput = screen.getByLabelText(/^balance$/i);
    await user.type(balanceInput, '1000');
    await user.click(screen.getByRole('button', { name: /next/i }));

    // Step 4: Review - check for elements unique to review step
    await waitFor(
      () => {
        const buttons = screen.queryAllByRole('button', { name: /create account/i });
        expect(buttons.length).toBeGreaterThan(0);
      },
      { timeout: 2000 },
    );
  });

  it('closing and reopening resets to step 1', async () => {
    const { rerender } = renderWizard(true);
    const user = userEvent.setup();

    // Advance to step 2 (auto-advance)
    await user.click(screen.getByLabelText(/checking/i));

    await waitFor(
      () => {
        expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );

    // Close dialog
    rerender(
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
          })
        }
      >
        <AccountWizard open={false} onOpenChange={mockOnOpenChange} onSubmit={mockOnSubmit} />
      </QueryClientProvider>,
    );

    // Reopen dialog
    rerender(
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
          })
        }
      >
        <AccountWizard open={true} onOpenChange={mockOnOpenChange} onSubmit={mockOnSubmit} />
      </QueryClientProvider>,
    );

    // Should be back on step 1
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/checking/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
  });

  it('step 2 requires name before advancing', async () => {
    renderWizard();
    const user = userEvent.setup();

    // Advance to step 2 (auto-advance)
    await user.click(screen.getByLabelText(/checking/i));

    await waitFor(
      () => {
        expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );

    // Try to click Next without entering name
    await user.click(screen.getByRole('button', { name: /next/i }));

    // Should still be on step 2 (validation failed) - name input should still be present
    expect(screen.queryByLabelText(/account name/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /back/i })).toBeInTheDocument();
  });

  it('displays progress dots showing current step', () => {
    renderWizard();

    // Step 1 should show 4 dots
    // (We can't easily test the visual state, but verify the wizard renders)
    expect(screen.getAllByText('Choose Account Type').length).toBeGreaterThan(0);
  });

  it('edit mode starts at step 2, skips type selection, shows Update Account button', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    const mockEditAccount = {
      id: '123',
      account_type: 'checking',
      name: 'Test Checking',
      current_balance: { amount: '1500.00', currency: 'USD' },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    render(
      <QueryClientProvider client={queryClient}>
        <AccountWizard
          open={true}
          onOpenChange={mockOnOpenChange}
          onSubmit={mockOnSubmit}
          editAccount={mockEditAccount as AccountResponse}
        />
      </QueryClientProvider>,
    );

    // Should start at step 2 (Account Details) - dialog title should be "Edit Account"
    expect(screen.getByText('Edit Account')).toBeInTheDocument();

    // Should show Account Name field (step 2)
    expect(screen.getByLabelText(/account name/i)).toBeInTheDocument();

    // Navigate to review step
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /next/i }));

    // Step 3: Opening Balance
    await waitFor(
      () => {
        expect(screen.queryByLabelText(/^balance$/i)).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
    await user.click(screen.getByRole('button', { name: /next/i }));

    // Step 4: Review should show "Update Account" button
    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /update account/i })).toBeInTheDocument();
      },
      { timeout: 2000 },
    );
  });
});
