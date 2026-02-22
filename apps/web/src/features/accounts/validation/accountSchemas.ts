/**
 * Per-step Zod validation schemas for account wizard.
 * Each step validates independently for progressive validation.
 */
import { z } from 'zod';

// Step 1: Account type selection
export const stepTypeSchema = z.object({
  accountType: z.enum([
    'checking',
    'savings',
    'credit_card',
    'loan',
    'brokerage',
    'ira',
    'rewards',
  ]),
});

// Step 2: Account details (conditional fields based on type)
export const stepDetailsSchema = z.object({
  name: z.string().min(1, 'Account name is required').max(100, 'Name cannot exceed 100 characters'),
  creditLimit: z.string().optional(), // For credit cards
  apr: z
    .string()
    .optional()
    .refine(
      (val) => {
        if (!val) return true; // optional
        const num = parseFloat(val);
        return !isNaN(num) && num >= 0 && num <= 100;
      },
      { message: 'APR must be between 0 and 100' },
    ), // For loans (percentage)
  termMonths: z.string().optional(), // For loans
  subtype: z
    .enum([
      'traditional_ira',
      'roth_ira',
      'sep_ira',
      'mortgage',
      'auto_loan',
      'personal_loan',
      'line_of_credit',
    ])
    .optional(), // For IRAs and loans
  rewardsUnit: z.string().optional(), // For rewards accounts
});

// Step 3: Opening balance
export const stepBalanceSchema = z.object({
  openingBalance: z
    .string()
    .min(1, 'Opening balance is required')
    .refine((val) => !isNaN(parseFloat(val.replace(/[,$]/g, ''))), {
      message: 'Invalid amount',
    }),
  rewardsValue: z.string().optional(), // For rewards accounts (points/miles value)
});

// Step 4: Review (no validation - read-only confirmation)
export const stepReviewSchema = z.object({});

// Merged form data type across all steps
export type AccountFormData = z.infer<typeof stepTypeSchema> &
  z.infer<typeof stepDetailsSchema> &
  z.infer<typeof stepBalanceSchema>;

// Array of schemas for index-based access
export const stepSchemas = [
  stepTypeSchema,
  stepDetailsSchema,
  stepBalanceSchema,
  stepReviewSchema,
] as const;
