import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/__tests__/setup";
import { AuthProvider, useAuth } from "./auth-context";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

const BASE_URL = "http://localhost:8000";

// Helper: create a fake JWT with given payload
function createFakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(payload));
  const signature = "fake_signature";
  return `${header}.${body}.${signature}`;
}

function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("Auth Context", () => {
  beforeEach(() => {
    localStorage.clear();
    mockPush.mockClear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe("Initial state (no stored tokens)", () => {
    it("starts with isLoading true then resolves to unauthenticated", async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe("On mount with stored tokens", () => {
    it("sets authenticated state when valid token is in localStorage", async () => {
      const token = createFakeJwt({
        sub: "user-123",
        exp: Math.floor(Date.now() / 1000) + 3600,
        name: "María",
        email: "maria@example.com",
      });

      localStorage.setItem("access_token", token);
      localStorage.setItem("refresh_token", "fake_refresh");
      localStorage.setItem(
        "user_info",
        JSON.stringify({ id: "user-123", name: "María", email: "maria@example.com" })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({
        id: "user-123",
        name: "María",
        email: "maria@example.com",
      });
    });

    it("clears tokens and sets unauthenticated when token is expired", async () => {
      const token = createFakeJwt({
        sub: "user-123",
        exp: Math.floor(Date.now() / 1000) - 3600, // expired
      });

      localStorage.setItem("access_token", token);
      localStorage.setItem("refresh_token", "fake_refresh");

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(localStorage.getItem("access_token")).toBeNull();
      expect(localStorage.getItem("refresh_token")).toBeNull();
    });
  });

  describe("login()", () => {
    it("stores tokens and sets authenticated state on success", async () => {
      const accessToken = createFakeJwt({
        sub: "user-456",
        exp: Math.floor(Date.now() / 1000) + 3600,
        name: "Carlos",
        email: "carlos@example.com",
      });

      server.use(
        http.post(`${BASE_URL}/auth/login`, () => {
          return HttpResponse.json({
            access_token: accessToken,
            refresh_token: "new_refresh_token",
            token_type: "bearer",
          });
        })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login("carlos@example.com", "SecurePass123!");
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user?.id).toBe("user-456");
      expect(result.current.user?.email).toBe("carlos@example.com");
      expect(localStorage.getItem("access_token")).toBe(accessToken);
      expect(localStorage.getItem("refresh_token")).toBe("new_refresh_token");
    });

    it("uses login email as fallback when token lacks email claim", async () => {
      const accessToken = createFakeJwt({
        sub: "user-789",
        exp: Math.floor(Date.now() / 1000) + 3600,
        // no name or email claims
      });

      server.use(
        http.post(`${BASE_URL}/auth/login`, () => {
          return HttpResponse.json({
            access_token: accessToken,
            refresh_token: "refresh_token",
            token_type: "bearer",
          });
        })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login("user@test.com", "password");
      });

      expect(result.current.user?.email).toBe("user@test.com");
      expect(result.current.user?.id).toBe("user-789");
    });

    it("throws on invalid credentials", async () => {
      server.use(
        http.post(`${BASE_URL}/auth/login`, () => {
          return HttpResponse.json(
            { detail: "invalid_credentials" },
            { status: 401 }
          );
        })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.login("bad@email.com", "wrong");
        })
      ).rejects.toThrow();

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe("register()", () => {
    it("calls register endpoint and redirects to login on success", async () => {
      server.use(
        http.post(`${BASE_URL}/auth/register`, () => {
          return HttpResponse.json({ id: "new-user-id" }, { status: 201 });
        })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.register({
          name: "Nuevo Usuario",
          email: "nuevo@test.com",
          password: "SecurePass123!",
          consent_policy_version: "1.0",
          consent_purpose: "account_creation",
        });
      });

      // Should NOT set authenticated state
      expect(result.current.isAuthenticated).toBe(false);
      // Should redirect to login
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
  });

  describe("logout()", () => {
    it("clears tokens and state on logout", async () => {
      const token = createFakeJwt({
        sub: "user-123",
        exp: Math.floor(Date.now() / 1000) + 3600,
      });

      localStorage.setItem("access_token", token);
      localStorage.setItem("refresh_token", "refresh_to_revoke");
      localStorage.setItem(
        "user_info",
        JSON.stringify({ id: "user-123", name: "Test", email: "test@test.com" })
      );

      // Mock the logout endpoint (best-effort call)
      server.use(
        http.post(`${BASE_URL}/auth/logout`, () => {
          return new HttpResponse(null, { status: 204 });
        })
      );

      // Mock window.location.href setter
      const hrefSetter = vi.fn();
      Object.defineProperty(window, "location", {
        value: { ...window.location, href: "" },
        writable: true,
        configurable: true,
      });
      Object.defineProperty(window.location, "href", {
        set: hrefSetter,
        get: () => "",
        configurable: true,
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(localStorage.getItem("access_token")).toBeNull();
      expect(localStorage.getItem("refresh_token")).toBeNull();
      expect(localStorage.getItem("user_info")).toBeNull();
      expect(hrefSetter).toHaveBeenCalledWith("/login");
    });
  });

  describe("useAuth hook", () => {
    it("throws error when used outside AuthProvider", () => {
      expect(() => {
        renderHook(() => useAuth());
      }).toThrow("useAuth must be used within an AuthProvider");
    });
  });
});
