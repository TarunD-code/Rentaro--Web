/**
 * Centralized API Fetch Wrapper for Rentora
 * Handles:
 * 1. Automatic Authorization Header attachment (reads from in-memory token store)
 * 2. 401 Unauthorized -> Logout/Redirect
 * 3. 429 Too Many Requests -> Alert
 * 4. 503 Service Unavailable -> User-friendly error
 */

import { getAccessToken } from '../context/AuthContext';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

export const apiFetch = async (endpoint: string, options: RequestOptions = {}) => {
  // Read token from the in-memory store — not localStorage.
  // This prevents XSS payloads from exfiltrating credentials via localStorage.
  const token = getAccessToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      console.warn('Unauthorized request. Clearing session.');
      // Clear in-memory token + any legacy localStorage remnants
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      window.dispatchEvent(new Event('auth-logout'));
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
      return null;
    }

    if (response.status === 429) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Too many requests. Please slow down.');
    }

    if (response.status >= 500) {
      throw new Error('Service is currently unavailable. Please try again later.');
    }

    return response;
  } catch (error: any) {
    console.error(`API Fetch Error [${url}]:`, error);
    throw error;
  }
};

export const api = {
  get:    (url: string, options?: RequestOptions) =>
            apiFetch(url, { ...options, method: 'GET' }),
  post:   (url: string, data?: any, options?: RequestOptions) =>
            apiFetch(url, { ...options, method: 'POST', body: JSON.stringify(data) }),
  put:    (url: string, data?: any, options?: RequestOptions) =>
            apiFetch(url, { ...options, method: 'PUT', body: JSON.stringify(data) }),
  patch:  (url: string, data?: any, options?: RequestOptions) =>
            apiFetch(url, { ...options, method: 'PATCH', body: JSON.stringify(data) }),
  delete: (url: string, options?: RequestOptions) =>
            apiFetch(url, { ...options, method: 'DELETE' }),
};
