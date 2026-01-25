import { jwtDecode } from 'jwt-decode';

const TOKEN_STORAGE_KEY = 'diagramik_tokens';
const USER_STORAGE_KEY = 'diagramik_user';

interface JWTTokens {
  access: string;
  refresh: string;
}

interface User {
  pk: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

interface JWTPayload {
  exp: number;
  iat: number;
  jti: string;
  user_id: number;
}

export function getStoredTokens(): JWTTokens | null {
  if (typeof window === 'undefined') return null;

  const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored);
  } catch {
    return null;
  }
}

export function setTokens(tokens: JWTTokens): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;

  const stored = localStorage.getItem(USER_STORAGE_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored);
  } catch {
    return null;
  }
}

export function setUser(user: User): void {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function logout(): void {
  clearTokens();
  window.location.href = '/login';
}

export function isAuthenticated(): boolean {
  const tokens = getStoredTokens();
  if (!tokens) return false;

  // Check if access token is expired
  if (isTokenExpired(tokens.access)) {
    // Check if refresh token is also expired
    if (isTokenExpired(tokens.refresh)) {
      clearTokens();
      return false;
    }
    // Access token expired but refresh token valid - still authenticated
    // The API client will handle refreshing
    return true;
  }

  return true;
}

export function isTokenExpired(token: string): boolean {
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    // Add 10 second buffer
    return decoded.exp * 1000 < Date.now() + 10000;
  } catch {
    return true;
  }
}

export function getAccessToken(): string | null {
  const tokens = getStoredTokens();
  return tokens?.access ?? null;
}

export function getRefreshToken(): string | null {
  const tokens = getStoredTokens();
  return tokens?.refresh ?? null;
}

export function getAuthHeader(): string | null {
  const accessToken = getAccessToken();
  if (!accessToken) return null;
  return `Bearer ${accessToken}`;
}

export function getDisplayName(): string {
  const user = getStoredUser();
  if (!user) return '';
  return user.first_name || user.email.split('@')[0];
}
