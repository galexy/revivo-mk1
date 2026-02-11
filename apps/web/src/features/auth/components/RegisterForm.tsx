import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from '@tanstack/react-router';
import {
  Button,
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  Input,
} from '@workspace/ui';
import api from '../../../lib/api';
import { registerSchema, type RegisterFormData } from '../validation';
import { PasswordInput } from './PasswordInput';

export function RegisterForm() {
  const [isRegistered, setIsRegistered] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      displayName: '',
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setServerError(null);
      await api.post('/auth/register', {
        email: data.email,
        password: data.password,
        display_name: data.displayName,
      });
      // On success, show verification notice (do NOT auto-login)
      setIsRegistered(true);
    } catch (error: unknown) {
      // Extract error message from API response
      const axiosError = error as {
        response?: {
          status?: number;
          data?: { detail?: string | Array<{ loc?: string[]; msg?: string }> };
        };
      };
      if (axiosError?.response?.status === 422) {
        // Validation error - show field-level errors
        const validationErrors = axiosError.response.data?.detail;
        if (Array.isArray(validationErrors)) {
          // FastAPI returns array of {loc, msg, type}
          validationErrors.forEach((err) => {
            const field = err.loc?.[1]; // ["body", "email"] -> "email"
            if (field === 'email' || field === 'password' || field === 'display_name') {
              const formField = field === 'display_name' ? 'displayName' : field;
              form.setError(formField as keyof RegisterFormData, {
                message: err.msg,
              });
            }
          });
        } else {
          setServerError('Validation failed. Please check your input.');
        }
      } else {
        const message =
          (typeof axiosError?.response?.data?.detail === 'string'
            ? axiosError.response.data.detail
            : null) || 'Registration failed. Please try again.';
        setServerError(message);
      }
    }
  };

  // If registered, show verification notice
  if (isRegistered) {
    return (
      <div className="space-y-4 text-center">
        <div className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-4 dark:border-emerald-800/50 dark:bg-emerald-950/30">
          <svg viewBox="0 0 20 20" fill="currentColor" className="size-5 shrink-0 text-emerald-600 dark:text-emerald-400">
            <path fillRule="evenodd" d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.857-9.809a.75.75 0 0 0-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 1 0-1.06 1.061l2.5 2.5a.75.75 0 0 0 1.137-.089l4-5.5Z" clipRule="evenodd" />
          </svg>
          <p className="text-sm text-emerald-800 dark:text-emerald-200">
            Check your email to verify your account
          </p>
        </div>
        <Link to="/login" search={{}} className="inline-block text-sm font-medium text-primary hover:text-primary/80 transition-colors">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <FormField
          control={form.control}
          name="displayName"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-sm font-medium">Full name</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  placeholder="Jane Doe"
                  autoComplete="name"
                  className="h-11"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-sm font-medium">Email address</FormLabel>
              <FormControl>
                <Input
                  type="email"
                  placeholder="name@company.com"
                  autoComplete="email"
                  className="h-11"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-sm font-medium">Password</FormLabel>
              <FormControl>
                <PasswordInput
                  placeholder="Create a strong password"
                  autoComplete="new-password"
                  className="h-11"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {serverError && (
          <div className="flex items-center gap-2 rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
            <svg viewBox="0 0 20 20" fill="currentColor" className="size-4 shrink-0">
              <path fillRule="evenodd" d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16ZM8.28 7.22a.75.75 0 0 0-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 1 0 1.06 1.06L10 11.06l1.72 1.72a.75.75 0 1 0 1.06-1.06L11.06 10l1.72-1.72a.75.75 0 0 0-1.06-1.06L10 8.94 8.28 7.22Z" clipRule="evenodd" />
            </svg>
            {serverError}
          </div>
        )}

        <Button
          type="submit"
          className="h-11 w-full bg-gradient-to-r from-emerald-500 to-cyan-500 text-sm font-medium text-white shadow-lg shadow-emerald-500/25 transition-all hover:from-emerald-600 hover:to-cyan-600 hover:shadow-emerald-500/30"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting ? (
            <span className="flex items-center gap-2">
              <svg className="size-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-20" />
                <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
              Creating account...
            </span>
          ) : (
            'Create account'
          )}
        </Button>

        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-2 text-muted-foreground">or</span>
          </div>
        </div>

        <div className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" search={{}} className="font-medium text-primary hover:text-primary/80 transition-colors">
            Sign in
          </Link>
        </div>
      </form>
    </Form>
  );
}
