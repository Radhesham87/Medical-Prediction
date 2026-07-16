import type { AuthResponse, Role } from "@/types";

const TOKEN_KEY = "neet_token";
const ROLE_KEY = "neet_role";
const NAME_KEY = "neet_name";

export function saveAuth(auth: AuthResponse) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, auth.access_token);
  localStorage.setItem(ROLE_KEY, auth.role);
  localStorage.setItem(NAME_KEY, auth.name);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getRole(): Role | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ROLE_KEY) as Role | null;
}

export function getName(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(NAME_KEY);
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  [TOKEN_KEY, ROLE_KEY, NAME_KEY].forEach((k) => localStorage.removeItem(k));
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
