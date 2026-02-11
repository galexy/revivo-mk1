import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createRouter, Navigate, RouterProvider } from '@tanstack/react-router';
import { AuthProvider } from './features/auth/context/AuthContext';
import { useAuth } from './features/auth/context/useAuth';
import { routeTree } from './routes';

// Self-hosted fonts
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/700.css';

// Global styles (Tailwind v4 + theme)
import './styles/globals.css';

// Create router
const router = createRouter({
  routeTree,
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- provided by InnerApp at runtime
  context: { auth: undefined! },
  defaultNotFoundComponent: () => <Navigate to="/" />,
});

// Register router type for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

// Inner component that provides auth context to router.
// RouterProvider calls router.update() during render, so whenever auth state
// changes and InnerApp re-renders, the router context is updated synchronously
// before any effects fire. No manual router.invalidate() needed.
function InnerApp() {
  const auth = useAuth();
  return <RouterProvider router={router} context={{ auth }} />;
}

const root = document.getElementById('root');
if (!root) throw new Error('Root element not found');

createRoot(root).render(
  <StrictMode>
    <AuthProvider>
      <InnerApp />
    </AuthProvider>
  </StrictMode>
);
