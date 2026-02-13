/**
 * Account Wizard Modal
 * 4-step wizard for creating and editing accounts.
 * Supports all 7 account types with type-specific fields.
 */
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@workspace/ui';
import { ProgressDots } from './ProgressDots';
import { StepTypeSelection } from './AccountWizardSteps/StepTypeSelection';
import { StepDetails } from './AccountWizardSteps/StepDetails';
import { StepOpeningBalance } from './AccountWizardSteps/StepOpeningBalance';
import { StepReview } from './AccountWizardSteps/StepReview';
import {
  stepSchemas,
  type AccountFormData,
} from '../validation/accountSchemas';
import type { AccountResponse } from '@/lib/api-client';

interface AccountWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editAccount?: AccountResponse;
  onSubmit: (data: AccountFormData) => void;
}

const stepTitles = [
  'Choose Account Type',
  'Account Details',
  'Opening Balance',
  'Review & Confirm',
];

export function AccountWizard({
  open,
  onOpenChange,
  editAccount,
  onSubmit,
}: AccountWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Partial<AccountFormData>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm({
    resolver: zodResolver(stepSchemas[currentStep]) as any,
    defaultValues: formData,
    mode: 'onChange',
  });

  // Reset form when dialog closes
  useEffect(() => {
    if (!open) {
      setCurrentStep(0);
      setFormData({});
      form.reset();
      setIsSubmitting(false);
    }
  }, [open, form]);

  // Populate form data when editing
  useEffect(() => {
    if (editAccount && open) {
      const editData: Partial<AccountFormData> = {
        accountType: editAccount.account_type as any,
        name: editAccount.name,
        openingBalance: editAccount.current_balance.amount,
      };

      // Add type-specific fields
      if (editAccount.credit_limit) {
        editData.creditLimit = editAccount.credit_limit.amount;
      }
      if (editAccount.apr) {
        // Convert APR from decimal (API returns) to percentage (form displays)
        editData.apr = (parseFloat(editAccount.apr) * 100).toString();
      }
      if (editAccount.term_months) {
        editData.termMonths = editAccount.term_months.toString();
      }
      if (editAccount.subtype) {
        editData.subtype = editAccount.subtype as any;
      }
      if ('rewards_unit' in editAccount && (editAccount as any).rewards_unit) {
        editData.rewardsUnit = (editAccount as any).rewards_unit;
      }

      setFormData(editData);
      form.reset(editData);
    }
  }, [editAccount, open, form]);

  const goToNextStep = async () => {
    const isValid = await form.trigger();
    if (isValid) {
      const currentValues = form.getValues();
      setFormData({ ...formData, ...currentValues });
      setCurrentStep((prev) => Math.min(prev + 1, stepSchemas.length - 1));
      form.clearErrors();
    }
  };

  const goToPreviousStep = () => {
    const currentValues = form.getValues();
    setFormData({ ...formData, ...currentValues });
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const finalData = { ...formData, ...form.getValues() } as AccountFormData;
      await onSubmit(finalData);
      onOpenChange(false);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const accountType = formData.accountType || form.watch('accountType') || '';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <ProgressDots currentStep={currentStep} totalSteps={4} />
          <DialogTitle className="text-center">
            {editAccount ? 'Edit Account' : stepTitles[currentStep]}
          </DialogTitle>
        </DialogHeader>

        <div className="mt-4">
          {currentStep === 0 && (
            <StepTypeSelection form={form} onNext={goToNextStep} />
          )}
          {currentStep === 1 && (
            <StepDetails
              form={form}
              accountType={accountType}
              onNext={goToNextStep}
              onBack={goToPreviousStep}
            />
          )}
          {currentStep === 2 && (
            <StepOpeningBalance
              form={form}
              accountType={accountType}
              onNext={goToNextStep}
              onBack={goToPreviousStep}
            />
          )}
          {currentStep === 3 && (
            <StepReview
              formData={formData}
              onSubmit={handleSubmit}
              onBack={goToPreviousStep}
              isSubmitting={isSubmitting}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
