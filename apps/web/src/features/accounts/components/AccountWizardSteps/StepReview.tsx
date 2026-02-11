/**
 * Step 4: Review
 * Shows read-only summary of all entered data before submission.
 */
import { Button, Separator } from '@workspace/ui';
import type { AccountFormData } from '../../validation/accountSchemas';

interface StepReviewProps {
  formData: Partial<AccountFormData>;
  onSubmit: () => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

const accountTypeLabels: Record<string, string> = {
  checking: 'Checking',
  savings: 'Savings',
  credit_card: 'Credit Card',
  loan: 'Loan',
  brokerage: 'Brokerage',
  ira: 'IRA',
  rewards: 'Rewards',
};

const subtypeLabels: Record<string, string> = {
  traditional_ira: 'Traditional IRA',
  roth_ira: 'Roth IRA',
  sep_ira: 'SEP IRA',
  mortgage: 'Mortgage',
  auto_loan: 'Auto Loan',
  personal_loan: 'Personal Loan',
  line_of_credit: 'Line of Credit',
};

export function StepReview({
  formData,
  onSubmit,
  onBack,
  isSubmitting = false,
}: StepReviewProps) {
  const accountTypeLabel =
    accountTypeLabels[formData.accountType || ''] || formData.accountType;

  const formatBalance = (balance: string | undefined, accountType: string) => {
    if (!balance) return '$0.00';
    if (accountType === 'rewards') return balance;
    const numValue = parseFloat(balance.replace(/[,$]/g, ''));
    return isNaN(numValue) ? balance : `$${numValue.toFixed(2)}`;
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Review & Confirm</h3>
        <p className="text-sm text-muted-foreground">
          Please review the details before creating your account
        </p>
      </div>

      <div className="space-y-4 rounded-lg border p-4">
        <div className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground">Account Type</p>
            <p className="font-medium">{accountTypeLabel}</p>
          </div>

          <Separator />

          <div>
            <p className="text-sm text-muted-foreground">Account Name</p>
            <p className="font-medium">{formData.name || '-'}</p>
          </div>

          {formData.creditLimit && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground">Credit Limit</p>
                <p className="font-medium">${formData.creditLimit}</p>
              </div>
            </>
          )}

          {formData.apr && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground">APR</p>
                <p className="font-medium">{formData.apr}%</p>
              </div>
            </>
          )}

          {formData.termMonths && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground">Term</p>
                <p className="font-medium">{formData.termMonths} months</p>
              </div>
            </>
          )}

          {formData.subtype && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground">Type</p>
                <p className="font-medium">
                  {subtypeLabels[formData.subtype] || formData.subtype}
                </p>
              </div>
            </>
          )}

          {formData.rewardsUnit && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground">Reward Unit</p>
                <p className="font-medium">{formData.rewardsUnit}</p>
              </div>
            </>
          )}

          <Separator />

          <div>
            <p className="text-sm text-muted-foreground">Opening Balance</p>
            <p className="font-medium">
              {formatBalance(
                formData.openingBalance,
                formData.accountType || '',
              )}
            </p>
          </div>
        </div>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack} disabled={isSubmitting}>
          Back
        </Button>
        <Button onClick={onSubmit} disabled={isSubmitting}>
          {isSubmitting ? 'Creating...' : 'Create Account'}
        </Button>
      </div>
    </div>
  );
}
