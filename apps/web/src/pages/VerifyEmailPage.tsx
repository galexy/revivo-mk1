import { useEffect, useState } from 'react';
import { useSearch, useNavigate } from '@tanstack/react-router';
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label } from '@workspace/ui';
import api from '../lib/api';
import type { VerifyEmailResponse, RegisterResponse } from '../features/auth/types';

type VerifyState = 'loading' | 'success' | 'error' | 'expired';

export function VerifyEmailPage() {
  const navigate = useNavigate();
  const { token } = useSearch({ from: '/verify' });
  const [state, setState] = useState<VerifyState>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setState('error');
      setErrorMessage('No verification token provided');
      return;
    }

    const verifyToken = async () => {
      try {
        await api.get<VerifyEmailResponse>(`/auth/verify?token=${encodeURIComponent(token)}`);
        setState('success');
      } catch (error: any) {
        const message = error.response?.data?.detail || 'Verification failed';
        setErrorMessage(message);
        // Check if the error indicates an expired token
        if (message.toLowerCase().includes('expired')) {
          setState('expired');
        } else {
          setState('error');
        }
      }
    };

    verifyToken();
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resendEmail.trim()) return;

    setResending(true);
    setResendSuccess(false);

    try {
      // Re-register with the same email to trigger new verification email
      await api.post<RegisterResponse>('/auth/register', {
        email: resendEmail,
        password: 'placeholder', // Won't be used since user already exists
        display_name: 'placeholder', // Won't be used since user already exists
      });
      setResendSuccess(true);
      setResendEmail('');
    } catch (error: any) {
      // Silently succeed even on error (enumeration protection)
      // The API returns 202 for duplicate emails, so this should always succeed
      setResendSuccess(true);
      setResendEmail('');
    } finally {
      setResending(false);
    }
  };

  if (state === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">Verifying Email</CardTitle>
            <CardDescription>Please wait while we verify your email address...</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (state === 'success') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
              <svg
                className="h-6 w-6 text-green-600 dark:text-green-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <CardTitle className="text-2xl text-center">Email Verified</CardTitle>
            <CardDescription className="text-center">
              Your email has been successfully verified. You can now log in to your account.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" onClick={() => navigate({ to: '/login', search: {} })}>
              Continue to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (state === 'expired') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">Verification Link Expired</CardTitle>
            <CardDescription>
              This verification link has expired. Please enter your email below to receive a new verification link.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {resendSuccess ? (
              <div className="rounded-md bg-green-50 p-4 dark:bg-green-900/20">
                <p className="text-sm text-green-800 dark:text-green-300">
                  If an account exists with that email, a new verification link has been sent. Please check your inbox.
                </p>
              </div>
            ) : (
              <form onSubmit={handleResend} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="resend-email">Email</Label>
                  <Input
                    id="resend-email"
                    type="email"
                    placeholder="you@example.com"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    required
                    disabled={resending}
                  />
                </div>
                <Button type="submit" className="w-full" disabled={resending}>
                  {resending ? 'Sending...' : 'Resend Verification Email'}
                </Button>
              </form>
            )}
            <Button variant="outline" className="w-full" onClick={() => navigate({ to: '/login', search: {} })}>
              Back to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
            <svg
              className="h-6 w-6 text-red-600 dark:text-red-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <CardTitle className="text-2xl text-center">Verification Failed</CardTitle>
          <CardDescription className="text-center">{errorMessage}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" className="w-full" onClick={() => navigate({ to: '/login', search: {} })}>
            Back to Login
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
