/**
 * Tests for API error parsing utilities.
 */
import { describe, it, expect } from 'vitest';
import { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { parseApiError, getErrorMessage, isApiError } from './api-error';

describe('isApiError', () => {
  it('returns true for AxiosError', () => {
    const error = new AxiosError('Test error');
    expect(isApiError(error)).toBe(true);
  });

  it('returns false for non-Axios errors', () => {
    const error = new Error('Regular error');
    expect(isApiError(error)).toBe(false);
  });

  it('returns false for non-object values', () => {
    expect(isApiError('string')).toBe(false);
    expect(isApiError(null)).toBe(false);
    expect(isApiError(undefined)).toBe(false);
  });
});

describe('parseApiError', () => {
  it('parses validation error with object detail', () => {
    const error = new AxiosError('Validation failed');
    error.response = {
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
      data: {
        detail: {
          code: 'VALIDATION_ERROR',
          message: 'Name is required',
        },
      },
    };

    const result = parseApiError(error);

    expect(result).toEqual({
      status: 400,
      code: 'VALIDATION_ERROR',
      message: 'Name is required',
      isValidation: true,
      isServerError: false,
    });
  });

  it('parses auth error with string detail', () => {
    const error = new AxiosError('Unauthorized');
    error.response = {
      status: 401,
      statusText: 'Unauthorized',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
      data: {
        detail: 'Invalid credentials',
      },
    };

    const result = parseApiError(error);

    expect(result).toEqual({
      status: 401,
      code: 'API_ERROR',
      message: 'Invalid credentials',
      isValidation: true,
      isServerError: false,
    });
  });

  it('parses 404 error', () => {
    const error = new AxiosError('Not Found');
    error.response = {
      status: 404,
      statusText: 'Not Found',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
      data: {
        detail: {
          code: 'NOT_FOUND',
          message: 'Account not found',
        },
      },
    };

    const result = parseApiError(error);

    expect(result.status).toBe(404);
    expect(result.code).toBe('NOT_FOUND');
    expect(result.isValidation).toBe(true);
    expect(result.isServerError).toBe(false);
  });

  it('parses 500 server error', () => {
    const error = new AxiosError('Internal Server Error');
    error.response = {
      status: 500,
      statusText: 'Internal Server Error',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
      data: {
        detail: {
          code: 'INTERNAL_ERROR',
          message: 'Database connection failed',
        },
      },
    };

    const result = parseApiError(error);

    expect(result.status).toBe(500);
    expect(result.isValidation).toBe(false);
    expect(result.isServerError).toBe(true);
  });

  it('handles network error (no response)', () => {
    const error = new AxiosError('Network Error');
    // No response property = network error

    const result = parseApiError(error);

    expect(result).toEqual({
      status: 0,
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to server. Please check your connection.',
      isValidation: false,
      isServerError: false,
    });
  });

  it('handles unknown error (not AxiosError)', () => {
    const error = new Error('Something went wrong');

    const result = parseApiError(error);

    expect(result).toEqual({
      status: 500,
      code: 'UNKNOWN_ERROR',
      message: 'Something went wrong',
      isValidation: false,
      isServerError: true,
    });
  });

  it('handles malformed error response', () => {
    const error = new AxiosError('Bad error');
    error.response = {
      status: 500,
      statusText: 'Internal Server Error',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
      data: {}, // No detail field
    };

    const result = parseApiError(error);

    expect(result.status).toBe(500);
    expect(result.code).toBe('UNKNOWN_ERROR');
    expect(result.message).toBe('An unexpected error occurred');
  });
});

describe('getErrorMessage', () => {
  it('extracts message from validation error', () => {
    const error = new AxiosError('Validation failed');
    error.response = {
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
      data: {
        detail: {
          code: 'VALIDATION_ERROR',
          message: 'Name is required',
        },
      },
    };

    expect(getErrorMessage(error)).toBe('Name is required');
  });

  it('extracts message from server error', () => {
    const error = new AxiosError('Internal Server Error');
    error.response = {
      status: 500,
      statusText: 'Internal Server Error',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
      data: {
        detail: {
          code: 'INTERNAL_ERROR',
          message: 'Database error',
        },
      },
    };

    expect(getErrorMessage(error)).toBe('Database error');
  });

  it('extracts message from network error', () => {
    const error = new AxiosError('Network Error');

    expect(getErrorMessage(error)).toBe(
      'Unable to connect to server. Please check your connection.',
    );
  });

  it('handles unknown error', () => {
    const error = new Error('Random error');

    expect(getErrorMessage(error)).toBe('Random error');
  });
});
