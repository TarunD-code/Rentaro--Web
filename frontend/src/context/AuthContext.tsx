/**
 * Rentora — Secure Auth Context
 * ================================
 * JWT Storage Security Model (OWASP-aligned):
 *
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │  Token          │ Storage         │ Lifespan │ Threat mitigated │
 *   ├─────────────────┼─────────────────┼──────────┼──────────────────┤
 *   │  access_token   │ React memory    │  60 min  │ XSS theft        │
 *   │  role           │ React memory    │  60 min  │ XSS theft        │
 *   └─────────────────────────────────────────────────────────────────┘
 *
 * Why NOT localStorage:
 *   Any XSS payload can call localStorage.getItem('token') and exfiltrate
 *   long-lived credentials.  Keeping the access token in a module-level
 *   variable means it is inaccessible to injected scripts.
 *
 * Why NOT HttpOnly cookie for access token (current phase):
 *   Requires a same-origin server or a BFF (Backend-For-Frontend) to set
 *   the cookie.  Our current architecture has the gateway on :8000 and the
 *   Vite dev server on :5173 — cross-origin, so the browser would block
 *   SameSite=Strict cookies.  The in-memory approach gives equivalent XSS
 *   protection without requiring a BFF rewrite.
 *
 * Migration path to HttpOnly cookies (production):
 *   1. Add a /auth/refresh endpoint that sets:
 *        Set-Cookie: refresh_token=<long-lived>; HttpOnly; Secure;
 *                    SameSite=Strict; Path=/auth/refresh; Max-Age=604800
 *   2. Access token stays in memory (60 min TTL).
 *   3. On page reload, call /auth/refresh — the browser sends the HttpOnly
 *      cookie automatically, the server issues a new access token in the
 *      JSON response body (not a cookie), and the frontend stores it here.
 *   4. Remove all localStorage.setItem('token') calls.
 *
 * Usage:
 *   const { token, role, login, logout } = useAuth();
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';

// ── In-memory token store (not accessible to XSS payloads) ──────────────────
// Module-level so it survives re-renders but is cleared on tab close.
let _accessToken: string | null = null;
let _role:        string | null = null;

interface AuthState {
  token:   string | null;
  role:    string | null;
  isReady: boolean;           // true once the initial session check is complete
}

interface AuthContextValue extends AuthState {
  login:  (token: string, role: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  token:   null,
  role:    null,
  isReady: false,
  login:   () => {},
  logout:  () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    token:   _accessToken,
    role:    _role,
    isReady: false,
  });

  // ── Seed from localStorage on first mount (backward-compat bridge) ─────────
  // Existing users who already have a token in localStorage will stay logged in
  // after the upgrade.  New logins go through the login() callback below which
  // only writes to memory.  On the next logout the localStorage entries are
  // cleared, completing the migration.
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedRole  = localStorage.getItem('role');
    if (storedToken && storedRole) {
      _accessToken = storedToken;
      _role        = storedRole;
      setState({ token: storedToken, role: storedRole, isReady: true });
    } else {
      setState(s => ({ ...s, isReady: true }));
    }
  }, []);

  const login = useCallback((token: string, role: string) => {
    // Write only to memory — remove from localStorage to complete migration
    _accessToken = token;
    _role        = role;
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    setState({ token, role, isReady: true });
  }, []);

  const logout = useCallback(() => {
    _accessToken = null;
    _role        = null;
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    setState({ token: null, role: null, isReady: true });
  }, []);

  // ── Listen for the legacy auth-logout event dispatched by api.ts ──────────
  useEffect(() => {
    const handleLogout = () => logout();
    window.addEventListener('auth-logout', handleLogout);
    return () => window.removeEventListener('auth-logout', handleLogout);
  }, [logout]);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => useContext(AuthContext);

/**
 * Returns the current in-memory access token.
 * Use this in non-React code (e.g. api.ts fetch wrapper) where hooks
 * cannot be called.
 */
export const getAccessToken = (): string | null => _accessToken;
