import { useEffect } from 'react';
import {
  createRootRouteWithContext,
  createRoute,
  redirect,
  Outlet,
  useNavigate,
} from '@tanstack/react-router';
import type { QueryClient } from '@tanstack/react-query';
import type { AuthContextType } from './features/auth/context/AuthContext';
import { useAuth } from './features/auth/context/useAuth';
import { ProtectedRoute } from './features/auth/components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';
import { DashboardPage } from './pages/DashboardPage';
import { accountsQueryOptions } from './lib/query-options';

// Root route with auth and queryClient context injection
const rootRoute = createRootRouteWithContext<{
  auth: AuthContextType;
  queryClient: QueryClient;
}>()({
  component: () => <Outlet />,
});

// Public routes (no auth required)
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  validateSearch: (search: Record<string, unknown>): { expired?: boolean } => ({
    expired: search.expired === 'true' ? true : undefined,
  }),
  component: LoginPage,
});

const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: RegisterPage,
});

const verifyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/verify',
  validateSearch: (search: Record<string, unknown>): { token?: string } => ({
    token: search.token as string | undefined,
  }),
  component: VerifyEmailPage,
});

// Protected layout route — auth guard via beforeLoad
const protectedLayoutRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'protected',
  component: ProtectedRoute,
  beforeLoad: ({ context }) => {
    if (!context.auth.isLoading && !context.auth.isAuthenticated) {
      throw redirect({ to: '/login', search: {} });
    }
  },
});

const dashboardRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: '/dashboard',
  loader: ({ context }) => {
    // Prefetch accounts data for instant navigation
    // ensureQueryData returns cached data if fresh, or fetches if stale/missing
    context.queryClient.ensureQueryData(accountsQueryOptions);
  },
  component: DashboardPage,
});

// Index route component that redirects once auth state resolves
function IndexRedirect() {
  const { isLoading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading) {
      navigate({ to: isAuthenticated ? '/dashboard' : '/login' });
    }
  }, [isLoading, isAuthenticated, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="flex items-center gap-3 text-muted-foreground">
        <svg className="size-5 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="3"
            className="opacity-20"
          />
          <path
            d="M12 2a10 10 0 0 1 10 10"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
        <span>Loading...</span>
      </div>
    </div>
  );
}

// Root index route — redirect based on auth state
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: ({ context }) => {
    // If auth is already resolved, redirect immediately (avoids flash)
    if (!context.auth.isLoading) {
      throw redirect({ to: context.auth.isAuthenticated ? '/dashboard' : '/login' });
    }
    // Otherwise let the component handle it via useEffect
  },
  component: IndexRedirect,
});

// Build route tree
const routeTree = rootRoute.addChildren([
  loginRoute,
  registerRoute,
  verifyRoute,
  protectedLayoutRoute.addChildren([dashboardRoute]),
  indexRoute,
]);

export { routeTree };
export type { AuthContextType };
