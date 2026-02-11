/**
 * API error parsing utilities.
 *
 * Handles both FastAPI error formats:
 * - String detail (auth endpoints): { detail: "Invalid credentials" }
 * - Object detail (domain endpoints): { detail: { code: "...", message: "..." } }
 */
import type { AxiosError } from 'axios';

export interface ApiError {
  status: number;
  code: string;
  message: string;
  isValidation: boolean; // 4xx
  isServerError: boolean; // 5xx
}

/**
 * Type guard for Axios errors.
 */
export function isApiError(error: unknown): error is AxiosError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    error.isAxiosError === true
  );
}

/**
 * Parse unknown error into structured ApiError.
 *
 * Handles:
 * - AxiosError with response (4xx/5xx from API)
 * - AxiosError without response (network error)
 * - Unknown errors (fallback to generic server error)
 */
export function parseApiError(error: unknown): ApiError {
  // Network error (no response)
  if (isApiError(error) && !error.response) {
    return {
      status: 0,
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to server. Please check your connection.',
      isValidation: false,
      isServerError: false,
    };
  }

  // API error with response
  if (isApiError(error) && error.response) {
    const status = error.response.status;
    const data = error.response.data as { detail?: string | { code?: string; message?: string } };

    // Parse detail field (string or object)
    let code = 'UNKNOWN_ERROR';
    let message = 'An unexpected error occurred';

    if (typeof data.detail === 'string') {
      // String detail (auth endpoints)
      code = 'API_ERROR';
      message = data.detail;
    } else if (typeof data.detail === 'object' && data.detail !== null) {
      // Object detail (domain endpoints)
      code = data.detail.code || 'UNKNOWN_ERROR';
      message = data.detail.message || 'An unexpected error occurred';
    }

    return {
      status,
      code,
      message,
      isValidation: status >= 400 && status < 500,
      isServerError: status >= 500,
    };
  }

  // Unknown error (not Axios, or malformed)
  return {
    status: 500,
    code: 'UNKNOWN_ERROR',
    message: error instanceof Error ? error.message : 'An unexpected error occurred',
    isValidation: false,
    isServerError: true,
  };
}

/**
 * Extract user-friendly error message from unknown error.
 * Convenience function for displaying errors in UI.
 */
export function getErrorMessage(error: unknown): string {
  return parseApiError(error).message;
}
