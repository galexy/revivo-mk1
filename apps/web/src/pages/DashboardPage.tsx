/**
 * Dashboard page with account sidebar, wizard, and delete dialog.
 * Shows EmptyAccountsState when user has no accounts.
 */
import { useEffect, useState } from 'react';
import { Outlet } from '@tanstack/react-router';
import { UserMenu } from '../features/auth/components/UserMenu';
import { AccountSidebar } from '../features/accounts/components/AccountSidebar';
import { EmptyAccountsState } from '../features/accounts/components/EmptyAccountsState';
import { AccountWizard } from '../features/accounts/components/AccountWizard';
import { DeleteAccountDialog } from '../features/accounts/components/DeleteAccountDialog';
import { useAccounts } from '../features/accounts/hooks/useAccounts';
import { useCreateAccount } from '../features/accounts/hooks/useCreateAccount';
import { useUpdateAccount } from '../features/accounts/hooks/useUpdateAccount';
import { useDeleteAccount } from '../features/accounts/hooks/useDeleteAccount';
import type { AccountResponse } from '@/lib/api-client';
import type { AccountFormData } from '../features/accounts/validation/accountSchemas';

export function DashboardPage() {
  const { accounts, isLoading } = useAccounts();
  const createAccount = useCreateAccount();
  const updateAccount = useUpdateAccount();
  const deleteAccount = useDeleteAccount();

  const [isDark, setIsDark] = useState(() => {
    if (typeof window === 'undefined') return false;
    const stored = localStorage.getItem('theme');
    return (
      stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)
    );
  });

  const [wizardOpen, setWizardOpen] = useState(false);
  const [editAccount, setEditAccount] = useState<AccountResponse | undefined>(undefined);
  const [deleteAccountState, setDeleteAccountState] = useState<{
    id: string;
    name: string;
  } | null>(null);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const handleAddAccount = () => {
    setEditAccount(undefined);
    setWizardOpen(true);
  };

  const handleEditAccount = (accountId: string) => {
    const account = accounts.find((a) => a.id === accountId);
    if (account) {
      setEditAccount(account);
      setWizardOpen(true);
    }
  };

  const handleDeleteAccount = (accountId: string) => {
    const account = accounts.find((a) => a.id === accountId);
    if (account) {
      setDeleteAccountState({ id: account.id, name: account.name });
    }
  };

  const handleWizardSubmit = async (formData: AccountFormData) => {
    if (editAccount) {
      // Update existing account
      await updateAccount.mutateAsync({
        id: editAccount.id,
        data: { name: formData.name },
      });
    } else {
      // Create new account
      await createAccount.mutateAsync(formData);
    }
  };

  const handleConfirmDelete = async (id: string) => {
    await deleteAccount.mutateAsync(id);
    setDeleteAccountState(null);
  };

  // Show loading state while fetching initial accounts
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex items-center gap-3 text-muted-foreground">
          <svg className="size-5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="3"
              className="opacity-20"
            />
            <path
              d="M12 2a10 10 0 0 1 10 10"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Sidebar - only show if accounts exist */}
      {accounts.length > 0 && (
        <AccountSidebar
          accounts={accounts}
          onAddAccount={handleAddAccount}
          onEditAccount={handleEditAccount}
          onDeleteAccount={handleDeleteAccount}
          isDarkMode={isDark}
          onToggleDarkMode={() => setIsDark(!isDark)}
        />
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header with app title and user menu */}
        <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Personal Finance</h1>
          <UserMenu />
        </header>

        {/* Content area */}
        <div className="flex-1">
          {accounts.length === 0 ? (
            <EmptyAccountsState onAddAccount={handleAddAccount} />
          ) : (
            <Outlet />
          )}
        </div>
      </main>

      {/* Account Wizard Modal */}
      <AccountWizard
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        editAccount={editAccount}
        onSubmit={handleWizardSubmit}
      />

      {/* Delete Account Dialog */}
      {deleteAccountState && (
        <DeleteAccountDialog
          open={true}
          onOpenChange={(open) => {
            if (!open) setDeleteAccountState(null);
          }}
          accountName={deleteAccountState.name}
          accountId={deleteAccountState.id}
          onConfirmDelete={handleConfirmDelete}
        />
      )}
    </div>
  );
}
