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
        <div className="rounded-md bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 p-4">
          <p className="text-sm text-green-800 dark:text-green-200">
            Check your email to verify your account
          </p>
        </div>
        <Link to="/login" search={{}} className="inline-block text-sm text-primary hover:underline">
          Back to login
        </Link>
      </div>
    );
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="you@example.com" autoComplete="email" {...field} />
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
              <FormLabel>Password</FormLabel>
              <FormControl>
                <PasswordInput
                  placeholder="Create a password"
                  autoComplete="new-password"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="displayName"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Display Name</FormLabel>
              <FormControl>
                <Input type="text" placeholder="Your name" autoComplete="name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {serverError && (
          <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            {serverError}
          </div>
        )}

        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? 'Creating account...' : 'Create account'}
        </Button>

        <div className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" search={{}} className="text-primary hover:underline">
            Log in
          </Link>
        </div>
      </form>
    </Form>
  );
}
