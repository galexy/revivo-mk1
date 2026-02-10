import {
  createRootRouteWithContext,
  createRoute,
  redirect,
  Outlet,
} from '@tanstack/react-router';
import type { AuthContextType } from './features/auth/context/AuthContext';
import { ProtectedRoute } from './features/auth/components/ProtectedRoute';

// Root route with auth context injection
const rootRoute = createRootRouteWithContext<{ auth: AuthContextType }>()({
  component: () => <Outlet />,
});

// Public routes (no auth required)
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: () => <div>Login Page (placeholder)</div>, // Replaced in Plan 04
});

const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: () => <div>Register Page (placeholder)</div>, // Replaced in Plan 04
});

const verifyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/verify',
  component: () => <div>Verify Email (placeholder)</div>, // Replaced in Plan 05
});

// Protected layout route — auth guard via beforeLoad
const protectedLayoutRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'protected',
  component: ProtectedRoute,
  beforeLoad: ({ context }) => {
    if (!context.auth.isLoading && !context.auth.isAuthenticated) {
      throw redirect({ to: '/login' });
    }
  },
});

const dashboardRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: '/dashboard',
  component: () => <div>Dashboard (placeholder)</div>, // Replaced in Plan 05
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
