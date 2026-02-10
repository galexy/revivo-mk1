import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createMemoryHistory, createRouter, RouterProvider } from '@tanstack/react-router';
import { AuthContext, type AuthContextType } from '../features/auth/context/AuthContext';
import { routeTree } from '../routes';

// Mock the api module
vi.mock('../lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
  setAccessToken: vi.fn(),
  getAccessToken: vi.fn(() => null),
}));

describe('App routing', () => {
  let mockAuthContext: AuthContextType;

  beforeEach(() => {
    mockAuthContext = {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    };
  });

  it('unauthenticated user at / is redirected to /login', async () => {
    const history = createMemoryHistory({ initialEntries: ['/'] });
    const router = createRouter({
      routeTree,
      history,
      context: { auth: mockAuthContext },
    });

    render(
      <AuthContext.Provider value={mockAuthContext}>
        <RouterProvider router={router} />
      </AuthContext.Provider>
    );

    // Wait for redirect to complete
    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login');
    });

    // Verify login page is rendered
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
    });
  });

  it('authenticated user at / is redirected to /dashboard', async () => {
    // Mock authenticated state
    mockAuthContext = {
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        display_name: 'Test User',
        email_verified: true,
        created_at: '2024-01-01T00:00:00Z',
        household: {
          id: 'household-123',
          name: 'Test Household',
          is_owner: true,
        },
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    };

    const history = createMemoryHistory({ initialEntries: ['/'] });
    const router = createRouter({
      routeTree,
      history,
      context: { auth: mockAuthContext },
    });

    render(
      <AuthContext.Provider value={mockAuthContext}>
        <RouterProvider router={router} />
      </AuthContext.Provider>
    );

    // Wait for redirect to complete
    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/dashboard');
    });

    // Verify dashboard page is rendered
    await waitFor(() => {
      expect(screen.getByText(/personal finance/i)).toBeInTheDocument();
    });
  });
});
