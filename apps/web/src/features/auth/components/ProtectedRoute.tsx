import { Outlet } from '@tanstack/react-router';
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
    // Silent redirect — no toast/message
    window.location.href = '/login';
    return null;
  }

  return <Outlet />;
}
