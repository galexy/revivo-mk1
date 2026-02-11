import { useEffect } from 'react';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useAuth } from '../features/auth/context/useAuth';
import { LoginForm } from '../features/auth/components/LoginForm';
import { AuthLayout } from '../features/auth/components/AuthLayout';

/** Mini sparkline SVG for the dashboard preview */
function Sparkline({ color, d }: { color: string; d: string }) {
  return (
    <svg viewBox="0 0 80 24" className="h-6 w-20">
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Floating mock dashboard card shown on the left panel */
function DashboardPreview() {
  return (
    <div className="relative mx-auto w-full max-w-md pb-8">
      {/* Main card */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.07] p-6 shadow-2xl backdrop-blur-xl">
        {/* Header row */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Net Worth</p>
            <p className="mt-1 text-2xl font-bold text-white">$48,291.54</p>
          </div>
          <div className="flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-semibold text-emerald-400">
            <svg viewBox="0 0 12 12" fill="currentColor" className="size-3">
              <path d="M6 2l4 5H2l4-5Z" />
            </svg>
            +12.4%
          </div>
        </div>

        {/* Account rows */}
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-xl bg-white/5 px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="flex size-8 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400">
                <svg viewBox="0 0 16 16" fill="currentColor" className="size-4">
                  <path d="M2 4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4Zm3 1a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1H5Zm0 3a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1H5Z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-white">Checking</p>
                <p className="text-xs text-slate-500">Primary account</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold tabular-nums text-white">$12,847.32</p>
              <Sparkline
                color="#34d399"
                d="M2 18 L12 14 L22 16 L32 10 L42 12 L52 8 L62 6 L72 4 L78 6"
              />
            </div>
          </div>

          <div className="flex items-center justify-between rounded-xl bg-white/5 px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="flex size-8 items-center justify-center rounded-lg bg-violet-500/20 text-violet-400">
                <svg viewBox="0 0 16 16" fill="currentColor" className="size-4">
                  <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1ZM5.5 7.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 0 1H6a.5.5 0 0 1-.5-.5ZM6 9a.5.5 0 0 0 0 1h2.5a.5.5 0 0 0 0-1H6Z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-white">Savings</p>
                <p className="text-xs text-slate-500">Emergency fund</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold tabular-nums text-white">$25,200.00</p>
              <Sparkline
                color="#a78bfa"
                d="M2 20 L12 18 L22 16 L32 15 L42 12 L52 10 L62 8 L72 5 L78 4"
              />
            </div>
          </div>

          <div className="flex items-center justify-between rounded-xl bg-white/5 px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="flex size-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
                <svg viewBox="0 0 16 16" fill="currentColor" className="size-4">
                  <path d="M8 1a.5.5 0 0 1 .5.5V2h3a2 2 0 0 1 2 2v1.5a2 2 0 0 1-2 2H8.5v1h2a2 2 0 0 1 2 2V12a2 2 0 0 1-2 2H8.5v.5a.5.5 0 0 1-1 0V14H5a2 2 0 0 1-2-2v-1.5a2 2 0 0 1 2-2h2.5v-1H5.5a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2H7.5v-.5A.5.5 0 0 1 8 1Z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-white">Investment</p>
                <p className="text-xs text-slate-500">Index funds</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold tabular-nums text-white">$10,244.22</p>
              <Sparkline
                color="#fbbf24"
                d="M2 12 L12 14 L22 10 L32 12 L42 8 L52 10 L62 6 L72 8 L78 4"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Floating budget pill */}
      <div className="absolute -bottom-3 right-4 rounded-xl border border-white/10 bg-slate-900/90 px-5 py-3 shadow-xl backdrop-blur-xl">
        <p className="text-xs text-slate-500">Monthly budget</p>
        <div className="mt-1 flex items-center gap-2">
          <div className="h-1.5 w-24 overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-[68%] rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400" />
          </div>
          <span className="text-xs font-medium text-emerald-400">68%</span>
        </div>
      </div>
    </div>
  );
}

function LoginHeroContent() {
  return (
    <div className="w-full max-w-md space-y-10">
      <div className="space-y-3 text-center">
        <h1 className="text-3xl font-bold leading-tight tracking-tight text-white xl:text-4xl">
          Your finances,{' '}
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            simplified.
          </span>
        </h1>
        <p className="text-base leading-relaxed text-slate-400">
          Track spending, manage budgets, and build wealth — the modern alternative to legacy
          desktop software.
        </p>
      </div>

      <DashboardPreview />
    </div>
  );
}

export function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const { expired } = useSearch({ from: '/login' });

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate({ to: '/dashboard' });
    }
  }, [isAuthenticated, isLoading, navigate]);

  return (
    <AuthLayout
      isLoading={isLoading}
      leftContent={<LoginHeroContent />}
      title="Welcome back"
      description="Sign in to your account to continue"
      footer="By signing in, you agree to our Terms of Service and Privacy Policy."
    >
      {expired && (
        <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800/50 dark:bg-amber-950/30">
          <svg
            viewBox="0 0 20 20"
            fill="currentColor"
            className="size-5 shrink-0 text-amber-600 dark:text-amber-500"
          >
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 6a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 6Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-sm text-amber-800 dark:text-amber-300">
            Your session has expired. Please sign in again.
          </p>
        </div>
      )}

      <LoginForm />
    </AuthLayout>
  );
}
