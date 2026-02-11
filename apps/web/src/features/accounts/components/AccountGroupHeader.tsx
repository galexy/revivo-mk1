/**
 * Account group header component showing category label and subtotal balance.
 * Clickable to collapse/expand the group.
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { formatCurrency } from '../utils';

interface AccountGroupHeaderProps {
  label: string;
  subtotal: number;
  defaultExpanded?: boolean;
  onToggle?: (expanded: boolean) => void;
}

export function AccountGroupHeader({
  label,
  subtotal,
  defaultExpanded = true,
  onToggle,
}: AccountGroupHeaderProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const handleToggle = () => {
    const newExpanded = !isExpanded;
    setIsExpanded(newExpanded);
    onToggle?.(newExpanded);
  };

  return (
    <button
      onClick={handleToggle}
      className="flex items-center justify-between w-full px-3 py-2 text-sm transition-colors hover:bg-accent rounded-md group"
    >
      <div className="flex items-center gap-2">
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
        <span className="text-muted-foreground font-medium">{label}</span>
      </div>
      <span className="font-bold font-mono text-sm">{formatCurrency(subtotal)}</span>
    </button>
  );
}
