/**
 * Step 1: Account Type Selection
 * Shows all 7 account types as radio cards with icons and descriptions.
 */
import { RadioGroup, RadioGroupItem } from '@workspace/ui';
import { Label } from '@workspace/ui';
import {
  Wallet,
  PiggyBank,
  CreditCard,
  Landmark,
  TrendingUp,
  Shield,
  Star,
  type LucideIcon,
} from 'lucide-react';
import type { UseFormReturn } from 'react-hook-form';
import type { AccountFormData } from '../../validation/accountSchemas';

interface AccountType {
  value: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

const accountTypes: AccountType[] = [
  {
    value: 'checking',
    label: 'Checking',
    description: 'Everyday spending and bill payments',
    icon: Wallet,
  },
  {
    value: 'savings',
    label: 'Savings',
    description: 'Short-term savings and emergency funds',
    icon: PiggyBank,
  },
  {
    value: 'credit_card',
    label: 'Credit Card',
    description: 'Credit card accounts with limits',
    icon: CreditCard,
  },
  {
    value: 'loan',
    label: 'Loan',
    description: 'Mortgages, auto loans, and personal loans',
    icon: Landmark,
  },
  {
    value: 'brokerage',
    label: 'Brokerage',
    description: 'Investment accounts and trading',
    icon: TrendingUp,
  },
  {
    value: 'ira',
    label: 'IRA',
    description: 'Individual retirement accounts',
    icon: Shield,
  },
  {
    value: 'rewards',
    label: 'Rewards',
    description: 'Points, miles, and cashback tracking',
    icon: Star,
  },
];

interface StepTypeSelectionProps {
  form: UseFormReturn<Partial<AccountFormData>>;
  onNext: () => void;
}

export function StepTypeSelection({ form, onNext }: StepTypeSelectionProps) {
  const selectedType = form.watch('accountType');

  const handleTypeSelect = (value: string) => {
    form.setValue('accountType', value as AccountFormData['accountType']);
    // Auto-advance to next step after brief delay for visual feedback
    setTimeout(() => {
      onNext();
    }, 200);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Choose Account Type</h3>
        <p className="text-sm text-muted-foreground">Select the type of account you want to add</p>
      </div>

      <RadioGroup
        value={selectedType}
        onValueChange={handleTypeSelect}
        className="grid gap-3 sm:grid-cols-2"
      >
        {accountTypes.map((type) => {
          const Icon = type.icon;
          return (
            <div key={type.value}>
              <RadioGroupItem value={type.value} id={type.value} className="peer sr-only" />
              <Label
                htmlFor={type.value}
                className="flex cursor-pointer flex-col gap-2 rounded-lg border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary"
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-5 w-5" />
                  <span className="font-semibold">{type.label}</span>
                </div>
                <span className="text-xs text-muted-foreground">{type.description}</span>
              </Label>
            </div>
          );
        })}
      </RadioGroup>
    </div>
  );
}
