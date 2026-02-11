/**
 * Single account row component showing name and balance.
 * Supports active state, hover, and context menu actions.
 */
import { MoreVertical } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Button,
} from '@workspace/ui';
import { formatCurrency } from '../utils';
import type { AccountResponse } from '@/lib/api-client';

interface AccountListItemProps {
  account: AccountResponse;
  isActive?: boolean;
  onClick?: () => void;
  onEdit?: (accountId: string) => void;
  onDelete?: (accountId: string) => void;
}

export function AccountListItem({
  account,
  isActive = false,
  onClick,
  onEdit,
  onDelete,
}: AccountListItemProps) {
  const balance = parseFloat(account.current_balance.amount);
  const isNegative = balance < 0;

  return (
    <div
      className={`group flex items-center justify-between px-3 py-2 rounded-md transition-colors cursor-pointer ${
        isActive
          ? 'bg-accent text-accent-foreground'
          : 'hover:bg-accent hover:text-accent-foreground'
      }`}
      onClick={onClick}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm truncate">{account.name}</span>
          <span
            className={`text-sm font-mono ${isNegative ? 'text-destructive' : ''}`}
          >
            {formatCurrency(account.current_balance.amount)}
          </span>
        </div>
      </div>

      {(onEdit || onDelete) && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity ml-2"
              onClick={(e) => {
                e.stopPropagation();
              }}
            >
              <MoreVertical className="h-4 w-4" />
              <span className="sr-only">More options</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {onEdit && (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(account.id);
                }}
              >
                Edit
              </DropdownMenuItem>
            )}
            {onDelete && (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(account.id);
                }}
                className="text-destructive focus:text-destructive"
              >
                Delete
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
}
