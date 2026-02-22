/**
 * Step 2: Account Details
 * Shows name field and type-specific fields based on account type.
 */
import {
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@workspace/ui';
import type { UseFormReturn } from 'react-hook-form';
import type { AccountFormData } from '../../validation/accountSchemas';

interface StepDetailsProps {
  form: UseFormReturn<Partial<AccountFormData>>;
  accountType: string;
  onNext: () => void;
  onBack: () => void;
}

export function StepDetails({ form, accountType, onNext, onBack }: StepDetailsProps) {
  const {
    register,
    formState: { errors },
    watch,
    setValue,
  } = form;

  const subtype = watch('subtype');

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Account Details</h3>
        <p className="text-sm text-muted-foreground">
          Provide the basic information for your account
        </p>
      </div>

      <div className="space-y-4">
        {/* Account Name - always shown */}
        <div className="space-y-2">
          <Label htmlFor="name">Account Name</Label>
          <Input
            id="name"
            placeholder="e.g., Chase Checking"
            {...register('name')}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                onNext();
              }
            }}
          />
          {errors.name?.message && (
            <p className="text-sm text-destructive">{String(errors.name.message)}</p>
          )}
        </div>

        {/* Credit Card: Credit Limit */}
        {accountType === 'credit_card' && (
          <div className="space-y-2">
            <Label htmlFor="creditLimit">Credit Limit</Label>
            <Input
              id="creditLimit"
              type="text"
              placeholder="5000.00"
              {...register('creditLimit')}
            />
            {errors.creditLimit?.message && (
              <p className="text-sm text-destructive">{String(errors.creditLimit.message)}</p>
            )}
          </div>
        )}

        {/* Loan: APR, Term, Subtype */}
        {accountType === 'loan' && (
          <>
            <div className="space-y-2">
              <Label htmlFor="apr">APR (%)</Label>
              <Input id="apr" type="text" placeholder="3.5" {...register('apr')} />
              {errors.apr?.message && (
                <p className="text-sm text-destructive">{String(errors.apr.message)}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="termMonths">Term (months)</Label>
              <Input id="termMonths" type="text" placeholder="360" {...register('termMonths')} />
              {errors.termMonths?.message && (
                <p className="text-sm text-destructive">{String(errors.termMonths.message)}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="loanSubtype">Loan Type</Label>
              <Select
                value={subtype}
                onValueChange={(value) => setValue('subtype', value as AccountFormData['subtype'])}
              >
                <SelectTrigger id="loanSubtype">
                  <SelectValue placeholder="Select loan type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mortgage">Mortgage</SelectItem>
                  <SelectItem value="auto_loan">Auto Loan</SelectItem>
                  <SelectItem value="personal_loan">Personal Loan</SelectItem>
                  <SelectItem value="line_of_credit">Line of Credit</SelectItem>
                </SelectContent>
              </Select>
              {errors.subtype?.message && (
                <p className="text-sm text-destructive">{String(errors.subtype.message)}</p>
              )}
            </div>
          </>
        )}

        {/* IRA: Subtype */}
        {accountType === 'ira' && (
          <div className="space-y-2">
            <Label htmlFor="iraSubtype">IRA Type</Label>
            <Select
              value={subtype}
              onValueChange={(value) => setValue('subtype', value as AccountFormData['subtype'])}
            >
              <SelectTrigger id="iraSubtype">
                <SelectValue placeholder="Select IRA type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="traditional_ira">Traditional IRA</SelectItem>
                <SelectItem value="roth_ira">Roth IRA</SelectItem>
                <SelectItem value="sep_ira">SEP IRA</SelectItem>
              </SelectContent>
            </Select>
            {errors.subtype?.message && (
              <p className="text-sm text-destructive">{String(errors.subtype.message)}</p>
            )}
          </div>
        )}

        {/* Rewards: Rewards Unit */}
        {accountType === 'rewards' && (
          <div className="space-y-2">
            <Label htmlFor="rewardsUnit">Reward Unit Name</Label>
            <Input
              id="rewardsUnit"
              placeholder="e.g., Points, Miles, Cashback"
              {...register('rewardsUnit')}
            />
            {errors.rewardsUnit?.message && (
              <p className="text-sm text-destructive">{String(errors.rewardsUnit.message)}</p>
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
