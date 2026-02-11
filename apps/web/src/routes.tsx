import { createRootRouteWithContext, createRoute, redirect, Outlet } from '@tanstack/react-router';
import type { AuthContextType } from './features/auth/context/AuthContext';
import { ProtectedRoute } from './features/auth/components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';
import { DashboardPage } from './pages/DashboardPage';

// Root route with auth context injection
const rootRoute = createRootRouteWithContext<{ auth: AuthContextType }>()({
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
  component: DashboardPage,
});

// Root index route — redirect based on auth state
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: ({ context }) => {
    if (context.auth.isLoading) return; // let component handle loading
    throw redirect({ to: context.auth.isAuthenticated ? '/dashboard' : '/login' });
  },
  component: () => (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  ),
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
