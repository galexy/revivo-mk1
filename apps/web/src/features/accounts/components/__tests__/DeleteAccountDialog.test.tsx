import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeleteAccountDialog } from '../DeleteAccountDialog';

describe('DeleteAccountDialog', () => {
  const mockOnOpenChange = vi.fn();
  const mockOnConfirmDelete = vi.fn();

  const defaultProps = {
    open: true,
    onOpenChange: mockOnOpenChange,
    accountName: 'My Checking Account',
    accountId: 'acc_123',
    onConfirmDelete: mockOnConfirmDelete,
  };

  const renderDialog = (props = defaultProps) => {
    return render(<DeleteAccountDialog {...props} />);
  };

  it('Delete button is disabled initially', () => {
    renderDialog();

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    expect(deleteButton).toBeDisabled();
  });

  it('typing wrong text keeps button disabled', async () => {
    renderDialog();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText(/type "my checking account" to confirm/i);
    await user.type(input, 'wrong text');

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    expect(deleteButton).toBeDisabled();
  });

  it('typing exact name enables Delete button', async () => {
    renderDialog();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText(/type "my checking account" to confirm/i);
    await user.type(input, 'My Checking Account');

    await waitFor(() => {
      const deleteButton = screen.getByRole('button', { name: /delete account/i });
      expect(deleteButton).not.toBeDisabled();
    });
  });

  it('clicking Delete calls onConfirmDelete with accountId', async () => {
    renderDialog();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText(/type "my checking account" to confirm/i);
    await user.type(input, 'My Checking Account');

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    await user.click(deleteButton);

    expect(mockOnConfirmDelete).toHaveBeenCalledWith('acc_123');
  });

  it('closing dialog clears typed text', async () => {
    const { rerender } = renderDialog();
    const user = userEvent.setup();

    // Type some text
    const input = screen.getByPlaceholderText(/type "my checking account" to confirm/i);
    await user.type(input, 'My Checking Account');

    expect(input).toHaveValue('My Checking Account');

    // Close dialog
    rerender(<DeleteAccountDialog {...defaultProps} open={false} />);

    // Reopen dialog
    rerender(<DeleteAccountDialog {...defaultProps} open={true} />);

    // Input should be cleared
    await waitFor(() => {
      const newInput = screen.getByPlaceholderText(/type "my checking account" to confirm/i);
      expect(newInput).toHaveValue('');
    });
  });

  it('displays account name in warning message', () => {
    renderDialog();

    expect(screen.getByText(/permanently delete the account/i)).toBeInTheDocument();
    // Account name appears multiple times (in description and input label)
    const accountNames = screen.getAllByText(/my checking account/i);
    expect(accountNames.length).toBeGreaterThan(0);
  });

  it('Cancel button calls onOpenChange', async () => {
    renderDialog();
    const user = userEvent.setup();

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('typing partial match keeps button disabled', async () => {
    renderDialog();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText(/type "my checking account" to confirm/i);
    await user.type(input, 'My Checking');

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    expect(deleteButton).toBeDisabled();
  });

  it('confirmation is case-sensitive', async () => {
    renderDialog();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText(/type "my checking account" to confirm/i);
    await user.type(input, 'my checking account'); // lowercase

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    expect(deleteButton).toBeDisabled();
  });
});
