/**
 * Account sidebar component showing grouped accounts with collapsible headers.
 * Includes "Add Account" button and dark mode toggle at bottom.
 */
import { useState } from 'react';
import { Plus, Sun, Moon } from 'lucide-react';
import { Button, Separator } from '@workspace/ui';
import { AccountGroupHeader } from './AccountGroupHeader';
import { AccountListItem } from './AccountListItem';
import { groupAccounts } from '../utils';
import type { AccountResponse } from '@/lib/api-client';

interface AccountSidebarProps {
  accounts: AccountResponse[];
  onAddAccount: () => void;
  onEditAccount?: (accountId: string) => void;
  onDeleteAccount?: (accountId: string) => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
}

export function AccountSidebar({
  accounts,
  onAddAccount,
  onEditAccount,
  onDeleteAccount,
  isDarkMode = false,
  onToggleDarkMode,
}: AccountSidebarProps) {
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    cash: true,
    credit: true,
    loans: true,
    investments: true,
    rewards: true,
  });

  // If no accounts, render nothing (EmptyAccountsState handles this in main area)
  if (accounts.length === 0) {
    return null;
  }

  const accountGroups = groupAccounts(accounts);

  const handleGroupToggle = (category: string, expanded: boolean) => {
    setExpandedGroups((prev) => ({ ...prev, [category]: expanded }));
  };

  return (
    <aside className="w-[var(--sidebar-width)] border-r border-border bg-card p-4 flex flex-col gap-4">
      {/* Header with Add Account button */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-primary">Accounts</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={onAddAccount}
          className="h-8 w-8 p-0"
          title="Add Account"
        >
          <Plus className="h-4 w-4" />
          <span className="sr-only">Add Account</span>
        </Button>
      </div>

      {/* Account groups */}
      <nav className="flex-1 space-y-1 overflow-y-auto">
        {accountGroups.map((group, index) => (
          <div key={group.category}>
            {index > 0 && <Separator className="my-2" />}
            <AccountGroupHeader
              label={group.label}
              subtotal={group.subtotal}
              defaultExpanded={expandedGroups[group.category]}
              onToggle={(expanded) => handleGroupToggle(group.category, expanded)}
            />
            {expandedGroups[group.category] && (
              <div className="mt-1 space-y-0.5">
                {group.accounts.map((account) => (
                  <AccountListItem
                    key={account.id}
                    account={account}
                    isActive={selectedAccountId === account.id}
                    onClick={() => setSelectedAccountId(account.id)}
                    onEdit={onEditAccount}
                    onDelete={onDeleteAccount}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Dark mode toggle at bottom */}
      {onToggleDarkMode && (
        <div className="mt-auto pt-4 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleDarkMode}
            className="w-full justify-start"
          >
            {isDarkMode ? (
              <>
                <Sun className="h-4 w-4 mr-2" />
                Light Mode
              </>
            ) : (
              <>
                <Moon className="h-4 w-4 mr-2" />
                Dark Mode
              </>
            )}
          </Button>
        </div>
      )}
    </aside>
  );
}
