/**
 * Account detail page showing account information.
 * Placeholder for Phase 15+ - will show transactions, balance chart, etc.
 */
import { useParams } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { accountDetailQueryOptions } from '@/lib/query-options';
import { Card, CardContent, CardHeader, CardTitle } from '@workspace/ui';
import { formatCurrency } from '../features/accounts/utils';

export function AccountDetailPage() {
  const { accountId } = useParams({ from: '/protected/dashboard/accounts/$accountId' });
  const { data: account, isLoading } = useQuery(accountDetailQueryOptions(accountId));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
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
          <span>Loading account...</span>
        </div>
      </div>
    );
  }

  if (!account) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Account not found</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold">{account.name}</h2>
        <p className="text-sm text-muted-foreground">
          {account.account_type.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Current Balance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold font-mono">
            {formatCurrency(account.current_balance.amount)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <span className="text-sm text-muted-foreground">Account ID:</span>
            <p className="font-mono text-sm">{account.id}</p>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Opened:</span>
            <p className="text-sm">
              {new Date(account.opening_date).toLocaleDateString()}
            </p>
          </div>
          {account.account_number_last4 && (
            <div>
              <span className="text-sm text-muted-foreground">Account Number (Last 4):</span>
              <p className="font-mono text-sm">****{account.account_number_last4}</p>
            </div>
          )}
          {account.institution && (
            <div>
              <span className="text-sm text-muted-foreground">Institution:</span>
              <p className="text-sm">{account.institution.name}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="text-center text-muted-foreground py-8">
        <p>Transactions and other account features coming in future phases.</p>
      </div>
    </div>
  );
}
