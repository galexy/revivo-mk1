import { createContext, useState, useEffect, ReactNode } from 'react';
import api, { setAccessToken } from '../../../lib/api';
import type { UserProfile, TokenResponse } from '../types';

export interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe: boolean) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Optimistic token refresh on mount
  useEffect(() => {
    const controller = new AbortController();

    const attemptRefresh = async () => {
      try {
        // Attempt silent refresh with existing cookie
        const refreshResponse = await api.post<TokenResponse>(
          '/auth/refresh',
          {},
          { signal: controller.signal }
        );

        // Store new access token
        setAccessToken(refreshResponse.data.access_token);

        // Fetch user profile
        const profileResponse = await api.get<UserProfile>(
          '/auth/me',
          { signal: controller.signal }
        );

        setUser(profileResponse.data);
      } catch {
        // Refresh failed or was aborted - user stays null (not authenticated)
        // This is expected for users without valid refresh cookie
        setUser(null);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    attemptRefresh();

    // Cleanup: abort in-flight requests on unmount (prevents StrictMode race)
    return () => {
      controller.abort();
    };
  }, []);

  const login = async (email: string, password: string, rememberMe: boolean): Promise<void> => {
    // OAuth2PasswordRequestForm requires form-encoded body
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    formData.append('remember_me', String(rememberMe));

    // Call /auth/token with form-encoded body
    const tokenResponse = await api.post<TokenResponse>('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Store access token in memory
    setAccessToken(tokenResponse.data.access_token);

    // Fetch user profile
    const profileResponse = await api.get<UserProfile>('/auth/me');
    setUser(profileResponse.data);
  };

  const logout = async (): Promise<void> => {
    try {
      // Call logout endpoint to clear server-side cookie
      await api.post('/auth/logout');
    } finally {
      // Always clear client-side state, even if logout endpoint fails
      setAccessToken(null);
      setUser(null);
      // Navigation is handled by the call site (e.g. UserMenu) using
      // router.invalidate() + navigate(), matching the official TanStack
      // Router authenticated-routes example pattern.
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
