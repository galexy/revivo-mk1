/**
 * Empty state component shown when the user has no accounts.
 * Displays a welcome message with a prominent call-to-action button.
 */
import { Wallet } from 'lucide-react';
import { Button } from '@workspace/ui';

interface EmptyAccountsStateProps {
  onAddAccount: () => void;
}

export function EmptyAccountsState({ onAddAccount }: EmptyAccountsStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center px-6">
      <div className="mb-6 rounded-full bg-muted p-6">
        <Wallet className="h-12 w-12 text-muted-foreground" />
      </div>

      <h2 className="text-2xl font-semibold mb-2">Welcome to Personal Finance</h2>

      <p className="text-muted-foreground mb-8 max-w-md">
        Add your first account to get started tracking your finances.
      </p>

      <Button size="lg" onClick={onAddAccount}>
        Add Your First Account
      </Button>
    </div>
  );
}
