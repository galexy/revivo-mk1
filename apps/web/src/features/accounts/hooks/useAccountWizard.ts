/**
 * Multi-step form state management hook for account wizard.
 * Handles step navigation, per-step validation, form data accumulation, and reset behavior.
 */
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  stepSchemas,
  type AccountFormData,
} from '../validation/accountSchemas';
import type { AccountResponse } from '@/lib/api-client';

export interface UseAccountWizardOptions {
  editAccount?: AccountResponse | null;
}

export interface UseAccountWizardReturn {
  currentStep: number;
  totalSteps: number;
  form: ReturnType<typeof useForm<Partial<AccountFormData>>>;
  formData: Partial<AccountFormData>;
  goToNextStep: () => Promise<void>;
  goToPreviousStep: () => void;
  reset: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
  isEditMode: boolean;
}

/**
 * Maps AccountResponse from API to form data structure.
 * Handles null/undefined gracefully for optional fields.
 */
function mapAccountToFormData(account: AccountResponse): Partial<AccountFormData> {
  const formData: Partial<AccountFormData> = {
    accountType: account.account_type as AccountFormData['accountType'],
    name: account.name,
    openingBalance: account.current_balance.amount,
  };

  // Add type-specific fields if present
  if (account.credit_limit) {
    formData.creditLimit = account.credit_limit.amount;
  }
  if (account.apr) {
    // Convert APR from decimal (API returns) to percentage (form displays)
    formData.apr = (parseFloat(account.apr) * 100).toString();
  }
  if (account.term_months) {
    formData.termMonths = account.term_months.toString();
  }
  if (account.subtype) {
    formData.subtype = account.subtype as AccountFormData['subtype'];
  }
  // Rewards unit (if exists in the response)
  if ('rewards_unit' in account && (account as any).rewards_unit) {
    formData.rewardsUnit = (account as any).rewards_unit;
  }

  return formData;
}

/**
 * Multi-step wizard hook with per-step Zod validation.
 *
 * Features:
 * - Step-by-step navigation with validation gates
 * - Form data persistence across steps
 * - Edit mode support (skips type selection step)
 * - Complete reset on dialog close
 *
 * @param options - Configuration options
 * @returns Wizard state and control functions
 */
export function useAccountWizard(
  options: UseAccountWizardOptions = {}
): UseAccountWizardReturn {
  const { editAccount } = options;

  // Edit mode skips step 0 (type selection)
  const initialStep = editAccount ? 1 : 0;
  const [currentStep, setCurrentStep] = useState(initialStep);

  // Accumulated form data across all steps
  const [formData, setFormData] = useState<Partial<AccountFormData>>(() => {
    if (editAccount) {
      return mapAccountToFormData(editAccount);
    }
    return {};
  });

  // React Hook Form with dynamic schema for current step
  const form = useForm<Partial<AccountFormData>>({
    resolver: zodResolver(stepSchemas[currentStep]) as any,
    defaultValues: formData,
    mode: 'onBlur',
  });

  // Reset form values when step changes
  // This ensures the form reflects accumulated data after navigation
  useEffect(() => {
    form.reset(formData);
  }, [currentStep, formData, form]);

  /**
   * Advance to next step after validating current step.
   * Only proceeds if current step's schema validation passes.
   */
  const goToNextStep = async () => {
    const isValid = await form.trigger();
    if (isValid) {
      // Merge current form values into accumulated data
      const currentValues = form.getValues();
      setFormData((prev) => ({ ...prev, ...currentValues }));

      // Advance step (capped at last step)
      setCurrentStep((prev) => Math.min(prev + 1, stepSchemas.length - 1));

      // Clear any validation errors from previous step
      form.clearErrors();
    }
  };

  /**
   * Go back to previous step, preserving current form values.
   * Edit mode cannot go back to step 0 (type selection is locked).
   */
  const goToPreviousStep = () => {
    // Save current values before navigating
    const currentValues = form.getValues();
    setFormData((prev) => ({ ...prev, ...currentValues }));

    // Go back (edit mode stops at step 1, create mode stops at step 0)
    setCurrentStep((prev) => Math.max(prev - 1, initialStep));
  };

  /**
   * Reset wizard to initial state.
   * Clears all form data and returns to first step.
   * Edit mode resets to edit data, create mode resets to empty.
   */
  const reset = () => {
    setCurrentStep(initialStep);
    const resetData = editAccount ? mapAccountToFormData(editAccount) : {};
    setFormData(resetData);
    form.reset(resetData);
  };

  // Calculate total steps (edit mode has 3 steps, create mode has 4)
  const totalSteps = editAccount ? 3 : 4;

  return {
    currentStep,
    totalSteps,
    form,
    formData: { ...formData, ...form.getValues() }, // Merge for latest values
    goToNextStep,
    goToPreviousStep,
    reset,
    isFirstStep: currentStep === initialStep,
    isLastStep: currentStep === stepSchemas.length - 1,
    isEditMode: !!editAccount,
  };
}
