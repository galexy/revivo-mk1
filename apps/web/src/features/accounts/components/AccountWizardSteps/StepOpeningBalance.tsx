/**
 * Step 3: Opening Balance
 * Shows currency input for monetary accounts or number input for rewards.
 */
import { Button, Input, Label } from '@workspace/ui';
import CurrencyInput from 'react-currency-input-field';
import type { UseFormReturn } from 'react-hook-form';
import type { AccountFormData } from '../../validation/accountSchemas';

interface StepOpeningBalanceProps {
  form: UseFormReturn<Partial<AccountFormData>>;
  accountType: string;
  onNext: () => void;
  onBack: () => void;
}

export function StepOpeningBalance({
  form,
  accountType,
  onNext,
  onBack,
}: StepOpeningBalanceProps) {
  const {
    register,
    formState: { errors },
    setValue,
    watch,
  } = form;

  const openingBalance = watch('openingBalance');
  const isRewardsAccount = accountType === 'rewards';

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Opening Balance</h3>
        <p className="text-sm text-muted-foreground">
          {isRewardsAccount
            ? 'Enter the current point/mile balance'
            : 'Enter the current balance for this account'}
        </p>
      </div>

      <div className="space-y-4">
        {isRewardsAccount ? (
          // Rewards: plain number input
          <div className="space-y-2">
            <Label htmlFor="openingBalance">Balance</Label>
            <Input
              id="openingBalance"
              type="text"
              placeholder="0"
              {...register('openingBalance')}
            />
            {errors.openingBalance?.message && (
              <p className="text-sm text-destructive">
                {String(errors.openingBalance.message)}
              </p>
            )}
          </div>
        ) : (
          // Monetary accounts: currency input
          <div className="space-y-2">
            <Label htmlFor="openingBalance">Balance</Label>
            <CurrencyInput
              id="openingBalance"
              name="openingBalance"
              placeholder="$0.00"
              prefix="$"
              decimalsLimit={2}
              value={openingBalance}
              onValueChange={(value) => {
                setValue('openingBalance', value || '');
              }}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
            />
            {errors.openingBalance?.message && (
              <p className="text-sm text-destructive">
                {String(errors.openingBalance.message)}
              </p>
            )}
          </div>
        )}
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onNext}>Next</Button>
      </div>
    </div>
  );
}
