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
  Checkbox,
} from '@workspace/ui';
import { useAuth } from '../context/useAuth';
import { loginSchema, type LoginFormData } from '../validation';
import { PasswordInput } from './PasswordInput';

export function LoginForm() {
  const { login } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setServerError(null);
      await login(data.email, data.password, data.rememberMe);
      // Navigation is handled by LoginPage's useEffect watching isAuthenticated.
      // By the time the effect fires, RouterProvider has already updated the
      // router context during render, so beforeLoad guards see the new auth state.
    } catch (error: unknown) {
      // Extract error message from API response
      const axiosError = error as { response?: { data?: { detail?: string } } };
      const message =
        axiosError?.response?.data?.detail || 'Login failed. Please try again.';
      setServerError(message);
    }
  };

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
                <Input
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
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
              <FormLabel>Password</FormLabel>
              <FormControl>
                <PasswordInput
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="rememberMe"
          render={({ field }) => (
            <FormItem className="flex items-center space-x-2 space-y-0">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <FormLabel className="cursor-pointer text-sm font-normal">
                Remember me
              </FormLabel>
            </FormItem>
          )}
        />

        {serverError && (
          <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            {serverError}
          </div>
        )}

        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? 'Logging in...' : 'Log in'}
        </Button>

        <div className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-primary hover:underline">
            Sign up
          </Link>
        </div>
      </form>
    </Form>
  );
}
