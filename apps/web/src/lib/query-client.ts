import { QueryClient } from '@tanstack/react-query';

/**
 * Default QueryClient configuration with sensible defaults.
 *
 * - staleTime: 30s default (accounts/categories change rarely)
 * - gcTime: 5min garbage collection for cached data
 * - retry: 1 (retry once, but NOT on 401 - Axios interceptor handles that)
 * - refetchOnWindowFocus: true for stale-while-revalidate behavior
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30 seconds
      gcTime: 5 * 60_000, // 5 minutes
      retry: (failureCount, error) => {
        // Don't retry on 401 errors (Axios interceptor handles token refresh)
        if (error && typeof error === 'object' && 'response' in error) {
          const axiosError = error as { response?: { status?: number } };
          if (axiosError.response?.status === 401) {
            return false;
          }
        }
        // Retry once for other errors
        return failureCount < 1;
      },
      refetchOnWindowFocus: true,
    },
    mutations: {
      // Don't retry mutations by default (they may have side effects)
      retry: false,
    },
  },
});

/**
 * Factory function for creating a fresh QueryClient instance.
 * Useful for tests to ensure isolation between test cases.
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        retry: (failureCount, error) => {
          if (error && typeof error === 'object' && 'response' in error) {
            const axiosError = error as { response?: { status?: number } };
            if (axiosError.response?.status === 401) {
              return false;
            }
          }
          return failureCount < 1;
        },
        refetchOnWindowFocus: true,
      },
      mutations: {
        retry: false,
      },
    },
  });
}
