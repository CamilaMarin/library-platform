"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  decodeTokenPayload,
} from "@/lib/token-storage";
import { apiPost } from "@/lib/api-client";
import type { LoginResponse, RegisterRequest, UserInfo } from "@/types";

// === Constants ===

const USER_INFO_KEY = "user_info";

// === Interfaces ===

interface AuthState {
  isAuthenticated: boolean;
  user: UserInfo | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login(email: string, password: string): Promise<void>;
  register(data: RegisterRequest): Promise<void>;
  logout(): void;
  updateUser(fields: Partial<Pick<UserInfo, "name" | "email">>): void;
}

// === Helpers ===

function storeUserInfo(user: UserInfo): void {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
}

function loadUserInfo(): UserInfo | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_INFO_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.id === "string") {
      return parsed as UserInfo;
    }
    return null;
  } catch {
    return null;
  }
}

function clearUserInfo(): void {
  localStorage.removeItem(USER_INFO_KEY);
}

/**
 * Decode user info from JWT payload.
 * The token payload may contain name and email claims beyond the standard sub/exp.
 * Falls back to stored user info if those claims are missing.
 */
function decodeUserFromToken(token: string): UserInfo | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;

    const payload = parts[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      "="
    );
    const decoded = atob(padded);
    const parsed = JSON.parse(decoded);

    if (typeof parsed.sub !== "string") return null;

    return {
      id: parsed.sub,
      name: typeof parsed.name === "string" ? parsed.name : "",
      email: typeof parsed.email === "string" ? parsed.email : "",
    };
  } catch {
    return null;
  }
}

// === Context ===

const AuthContext = createContext<AuthContextValue | null>(null);

// === Provider ===

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    isLoading: true,
  });

  // Check stored tokens on mount
  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      const payload = decodeTokenPayload(token);
      if (payload && payload.exp * 1000 > Date.now()) {
        // Token exists and is not expired
        const tokenUser = decodeUserFromToken(token);
        const storedUser = loadUserInfo();

        // Prefer stored user info (has name/email), fall back to token decode
        const user: UserInfo | null = storedUser ?? tokenUser;

        setState({
          isAuthenticated: true,
          user,
          isLoading: false,
        });
      } else {
        // Token expired — clear everything
        clearTokens();
        clearUserInfo();
        setState({ isAuthenticated: false, user: null, isLoading: false });
      }
    } else {
      setState({ isAuthenticated: false, user: null, isLoading: false });
    }
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const response = await apiPost<LoginResponse>("/auth/login", {
        email,
        password,
      });

      setTokens(response.access_token, response.refresh_token);

      // Decode user info from the access token
      const tokenUser = decodeUserFromToken(response.access_token);
      const user: UserInfo = {
        id: tokenUser?.id ?? "",
        name: tokenUser?.name ?? "",
        email: tokenUser?.email || email, // Use login email as fallback
      };

      storeUserInfo(user);

      setState({
        isAuthenticated: true,
        user,
        isLoading: false,
      });
    },
    []
  );

  const register = useCallback(
    async (data: RegisterRequest): Promise<void> => {
      await apiPost("/auth/register", data);
      // Do NOT auto-login — redirect to login page
      router.push("/login");
    },
    [router]
  );

  const logout = useCallback(() => {
    // Best-effort logout call to backend
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      apiPost("/auth/logout", { refresh_token: refreshToken }).catch(() => {
        // Ignore errors — we clear local state regardless
      });
    }

    clearTokens();
    clearUserInfo();
    setState({ isAuthenticated: false, user: null, isLoading: false });
    window.location.href = "/login";
  }, []);

  const updateUser = useCallback(
    (fields: Partial<Pick<UserInfo, "name" | "email">>) => {
      setState((prev) => {
        if (!prev.user) return prev;
        const updatedUser: UserInfo = { ...prev.user, ...fields };
        storeUserInfo(updatedUser);
        return { ...prev, user: updatedUser };
      });
    },
    []
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      register,
      logout,
      updateUser,
    }),
    [state, login, register, logout, updateUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// === Hook ===

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
