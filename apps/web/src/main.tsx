import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createRouter, RouterProvider } from '@tanstack/react-router';
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
  context: { auth: undefined! }, // will be provided by InnerApp
  defaultNotFoundComponent: () => {
    window.location.href = '/';
    return null;
  },
});

// Register router type for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

// Inner component that provides auth context to router
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
