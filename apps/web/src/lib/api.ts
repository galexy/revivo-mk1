import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { TokenResponse } from '../features/auth/types';

// Module-level token storage
let accessToken: string | null = null;

// Failed request queue for handling concurrent 401s
interface FailedRequest {
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}

let isRefreshing = false;
let failedQueue: FailedRequest[] = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else if (token) {
      promise.resolve(token);
    }
  });

  failedQueue = [];
};

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Send cookies cross-origin
});

// Request interceptor: attach Bearer token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor: handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // If not 401, reject immediately
    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    // Don't attempt token refresh for auth endpoints themselves:
    // - /auth/refresh: prevents infinite loop (refresh 401 → retry refresh → 401 → ...)
    // - /auth/token: 401 means wrong credentials, not expired session
    // - /auth/logout: no retry needed
    // Callers handle their own error display (e.g., LoginForm shows "Invalid credentials").
    if (originalRequest.url?.startsWith('/auth/')) {
      if (originalRequest.url.includes('/auth/refresh')) {
        accessToken = null;
      }
      return Promise.reject(error);
    }

    // If already retried, reject
    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    // If refresh is in progress, queue this request
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(api(originalRequest));
          },
          reject: (err: Error) => {
            reject(err);
          },
        });
      });
    }

    // Mark as retrying and start refresh
    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Call refresh endpoint (cookie is sent automatically via withCredentials)
      const response = await api.post<TokenResponse>('/auth/refresh');
      const newToken = response.data.access_token;

      // Update token
      accessToken = newToken;

      // Process queued requests
      processQueue(null, newToken);

      // Retry original request with new token
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
      }
      return api(originalRequest);
    } catch (refreshError) {
      // Refresh failed - clear token and redirect to login
      processQueue(refreshError as Error, null);
      accessToken = null;
      window.location.href = '/login?expired=true';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

// Token management functions
export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = () => accessToken;

export default api;
