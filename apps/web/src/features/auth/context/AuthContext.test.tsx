import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider } from './AuthContext';
import { useAuth } from './useAuth';
import type { UserProfile, TokenResponse } from '../types';

// Mock the api module - use factory function to avoid hoisting issues
vi.mock('../../../lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
  setAccessToken: vi.fn(),
  getAccessToken: vi.fn(() => null),
}));

// Import mocked api after mock is defined
import api, { setAccessToken as mockSetAccessToken } from '../../../lib/api';

const mockPost = api.post as ReturnType<typeof vi.fn>;
const mockGet = api.get as ReturnType<typeof vi.fn>;

// Test consumer component that displays auth state
function TestConsumer() {
  const auth = useAuth();

  return (
    <div>
      <div data-testid="isLoading">{String(auth.isLoading)}</div>
      <div data-testid="isAuthenticated">{String(auth.isAuthenticated)}</div>
      <div data-testid="user">{auth.user ? auth.user.email : 'null'}</div>
      <button onClick={() => auth.login('test@example.com', 'password', false)}>Login</button>
      <button onClick={() => auth.logout()}>Logout</button>
    </div>
  );
}

describe('AuthContext', () => {
  const mockUserProfile: UserProfile = {
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
  };

  const mockTokenResponse: TokenResponse = {
    access_token: 'mock-access-token',
    token_type: 'bearer',
    expires_in: 3600,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts in loading state', () => {
    // Mock refresh to never resolve so we stay in loading state
    mockPost.mockReturnValue(new Promise(() => {}));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    expect(screen.getByTestId('isLoading')).toHaveTextContent('true');
    expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('user')).toHaveTextContent('null');
  });

  it('attempts /auth/refresh on mount and sets user if successful', async () => {
    mockPost.mockResolvedValue({ data: mockTokenResponse });
    mockGet.mockResolvedValue({ data: mockUserProfile });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    // Wait for refresh to complete
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/auth/refresh', {}, expect.any(Object));
    });

    await waitFor(() => {
      expect(mockSetAccessToken).toHaveBeenCalledWith(mockTokenResponse.access_token);
      expect(mockGet).toHaveBeenCalledWith('/auth/me', expect.any(Object));
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent(mockUserProfile.email);
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
    });
  });

  it('sets isLoading to false after auth check completes', async () => {
    mockPost.mockResolvedValue({ data: mockTokenResponse });
    mockGet.mockResolvedValue({ data: mockUserProfile });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    // Initially loading
    expect(screen.getByTestId('isLoading')).toHaveTextContent('true');

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByTestId('isLoading')).toHaveTextContent('false');
    });
  });

  it('sets user to null if refresh fails (401)', async () => {
    mockPost.mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Invalid refresh token' },
      },
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    // Wait for refresh attempt to fail
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/auth/refresh', {}, expect.any(Object));
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('isLoading')).toHaveTextContent('false');
    });

    // Should not call setAccessToken or /auth/me on failure
    expect(mockSetAccessToken).not.toHaveBeenCalled();
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('login() calls /auth/token then /auth/me and updates user', async () => {
    // Mock refresh to fail (no existing session)
    mockPost.mockRejectedValueOnce({ response: { status: 401 } });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    // Wait for initial refresh to fail
    await waitFor(() => {
      expect(screen.getByTestId('isLoading')).toHaveTextContent('false');
    });

    // Now mock login flow
    mockPost.mockResolvedValueOnce({ data: mockTokenResponse });
    mockGet.mockResolvedValueOnce({ data: mockUserProfile });

    // Click login button
    const loginButton = screen.getByRole('button', { name: /login/i });
    loginButton.click();

    // Wait for login API calls
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/auth/token',
        expect.any(URLSearchParams),
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }),
      );
    });

    // Verify the form data
    const formData = mockPost.mock.calls[1][1] as URLSearchParams;
    expect(formData.get('username')).toBe('test@example.com');
    expect(formData.get('password')).toBe('password');
    expect(formData.get('remember_me')).toBe('false');

    await waitFor(() => {
      expect(mockSetAccessToken).toHaveBeenCalledWith(mockTokenResponse.access_token);
      expect(mockGet).toHaveBeenCalledWith('/auth/me');
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent(mockUserProfile.email);
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
    });
  });

  it('logout() calls /auth/logout and clears user', async () => {
    // Setup: start with authenticated user
    mockPost.mockResolvedValueOnce({ data: mockTokenResponse });
    mockGet.mockResolvedValueOnce({ data: mockUserProfile });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    // Wait for initial auth to complete
    await waitFor(() => {
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
    });

    // Mock logout endpoint
    mockPost.mockResolvedValueOnce({ data: { message: 'Logged out' } });

    // Click logout button
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    logoutButton.click();

    // Wait for logout call
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/auth/logout');
    });

    await waitFor(() => {
      expect(mockSetAccessToken).toHaveBeenCalledWith(null);
    });

    // Verify user is cleared (navigation is handled by the call site, not AuthContext)
    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
    });
  });
});
