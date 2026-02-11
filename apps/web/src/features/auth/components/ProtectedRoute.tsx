import { Navigate, Outlet } from '@tanstack/react-router';
import { useAuth } from '../context/useAuth';

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    // Neutral loading state while checking auth — prevents FOUC
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Fallback redirect if beforeLoad guard didn't catch this.
    // Navigate renders null and navigates in a useEffect (after render),
    // so the router context is already updated by this point.
    return <Navigate to="/login" />;
  }

  return <Outlet />;
}
