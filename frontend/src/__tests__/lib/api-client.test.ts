import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll, vi } from "vitest";
import * as fc from "fast-check";
import { ApiError, apiGet, setToastHandler } from "@/lib/api-client";
import { server } from "../setup";

// Disable MSW for this test file — we use vi.fn() mocks for fine-grained control
beforeAll(() => {
  server.close();
});

afterAll(() => {
  server.listen();
});

// === Mocks ===

// Mock token-storage module
const mockGetAccessToken = vi.fn<() => string | null>();
const mockGetRefreshToken = vi.fn<() => string | null>();
const mockSetTokens = vi.fn();
const mockClearTokens = vi.fn();

vi.mock("@/lib/token-storage", () => ({
  getAccessToken: () => mockGetAccessToken(),
  getRefreshToken: () => mockGetRefreshToken(),
  setTokens: (...args: unknown[]) => mockSetTokens(...args),
  clearTokens: () => mockClearTokens(),
}));

// Mock global fetch
const mockFetch = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", mockFetch);

// Track window.location.href assignments
let capturedHref: string | undefined;
const locationDescriptor = Object.getOwnPropertyDescriptor(window, "location");

beforeEach(() => {
  // Reset all mocks
  mockGetAccessToken.mockReturnValue(null);
  mockGetRefreshToken.mockReturnValue(null);
  mockSetTokens.mockReset();
  mockClearTokens.mockReset();
  mockFetch.mockReset();
  capturedHref = undefined;

  // Mock window.location.href setter
  Object.defineProperty(window, "location", {
    configurable: true,
    value: {
      ...window.location,
      href: window.location.href,
    },
    writable: true,
  });
  Object.defineProperty(window.location, "href", {
    configurable: true,
    set(value: string) {
      capturedHref = value;
    },
    get() {
      return capturedHref ?? "http://localhost:3000";
    },
  });
});

afterEach(() => {
  // Restore window.location
  if (locationDescriptor) {
    Object.defineProperty(window, "location", locationDescriptor);
  }
  // Reset toast handler
  setToastHandler(null as unknown as (message: string, type: "error") => void);
});

// Helper to create a Response-like object
function makeResponse(status: number, body?: unknown): Response {
  const headers = new Headers();
  const bodyStr = body !== undefined ? JSON.stringify(body) : "";
  if (bodyStr) {
    headers.set("content-length", String(bodyStr.length));
    headers.set("content-type", "application/json");
  }
  return new Response(bodyStr || null, { status, headers });
}

describe("API Client Property Tests", () => {
  /**
   * Property 1: Bearer token attachment
   * For any request when access token exists, Authorization header must equal `Bearer {token}`
   *
   * **Validates: Requirements 10.1**
   */
  describe("Property 1: Bearer token attachment", () => {
    it("attaches Bearer token to Authorization header for any token value", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1 }).filter((s) => s.trim().length > 0),
          async (token) => {
            mockFetch.mockReset();
            mockGetAccessToken.mockReturnValue(token);
            mockFetch.mockResolvedValueOnce(makeResponse(200, { ok: true }));

            await apiGet("/test");

            expect(mockFetch).toHaveBeenCalledTimes(1);
            const [, options] = mockFetch.mock.calls[0];
            const headers = options?.headers as Record<string, string>;
            expect(headers["Authorization"]).toBe(`Bearer ${token}`);
          }
        ),
        { numRuns: 10 }
      );
    });
  });

  /**
   * Property 2: Token refresh and retry on 401
   * For any 401 response, client calls refresh and retries exactly once
   *
   * **Validates: Requirements 1.8, 10.2**
   */
  describe("Property 2: Token refresh and retry on 401", () => {
    it("refreshes token and retries request exactly once on 401", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.webPath().filter((p) => p.length > 0),
          async (path) => {
            mockFetch.mockReset();
            mockSetTokens.mockReset();

            // Ensure path starts with /
            const normalizedPath = path.startsWith("/") ? path : `/${path}`;
            const refreshToken = "refresh-token-123";
            const newAccessToken = "new-access-token";

            mockGetAccessToken.mockReturnValue("expired-token");
            mockGetRefreshToken.mockReturnValue(refreshToken);

            // After setTokens is called, getAccessToken should return the new token
            mockSetTokens.mockImplementation(() => {
              mockGetAccessToken.mockReturnValue(newAccessToken);
            });

            // First call returns 401, refresh succeeds, retry succeeds
            mockFetch
              .mockResolvedValueOnce(makeResponse(401, { detail: "Unauthorized" }))
              .mockResolvedValueOnce(
                makeResponse(200, {
                  access_token: newAccessToken,
                  refresh_token: "new-refresh-token",
                })
              )
              .mockResolvedValueOnce(makeResponse(200, { data: "success" }));

            const result = await apiGet(normalizedPath);

            // Verify refresh was called
            const refreshCall = mockFetch.mock.calls[1];
            expect(refreshCall[0]).toContain("/auth/refresh");

            // Verify tokens were stored
            expect(mockSetTokens).toHaveBeenCalledWith(
              newAccessToken,
              "new-refresh-token"
            );

            // Verify total fetch calls: original + refresh + retry = 3
            expect(mockFetch).toHaveBeenCalledTimes(3);

            // Verify the retry used the new token
            const retryOptions = mockFetch.mock.calls[2][1];
            const retryHeaders = retryOptions?.headers as Record<string, string>;
            expect(retryHeaders["Authorization"]).toBe(`Bearer ${newAccessToken}`);

            expect(result).toEqual({ data: "success" });
          }
        ),
        { numRuns: 10 }
      );
    });
  });

  /**
   * Property 3: Failed refresh triggers logout
   * When refresh also fails, client clears tokens and redirects to `/login`
   *
   * **Validates: Requirements 1.9, 10.3**
   */
  describe("Property 3: Failed refresh triggers logout", () => {
    it("clears tokens and redirects to /login when refresh fails", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.webPath().filter((p) => p.length > 0),
          async (path) => {
            mockFetch.mockReset();
            mockClearTokens.mockReset();
            capturedHref = undefined;

            const normalizedPath = path.startsWith("/") ? path : `/${path}`;

            mockGetAccessToken.mockReturnValue("expired-token");
            mockGetRefreshToken.mockReturnValue("stale-refresh-token");

            // Original returns 401, refresh also fails
            mockFetch
              .mockResolvedValueOnce(makeResponse(401, { detail: "Unauthorized" }))
              .mockResolvedValueOnce(makeResponse(401, { detail: "Refresh failed" }));

            await expect(apiGet(normalizedPath)).rejects.toThrow();

            // Verify tokens were cleared
            expect(mockClearTokens).toHaveBeenCalled();

            // Verify redirect to /login
            expect(capturedHref).toBe("/login");
          }
        ),
        { numRuns: 10 }
      );
    });
  });

  /**
   * Property 4: Client error propagation
   * For any 4xx (non-401), error body is propagated unchanged
   *
   * **Validates: Requirements 1.6, 10.4**
   */
  describe("Property 4: Client error propagation", () => {
    it("propagates error body unchanged for any 4xx status (non-401)", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.integer({ min: 400, max: 499 }).filter((s) => s !== 401),
          fc.record({
            detail: fc.string({ minLength: 1 }),
            code: fc.string({ minLength: 1 }),
          }),
          async (status, errorBody) => {
            mockFetch.mockReset();
            mockGetAccessToken.mockReturnValue("valid-token");
            mockFetch.mockResolvedValueOnce(makeResponse(status, errorBody));

            try {
              await apiGet("/test");
              // Should not reach here
              expect.fail("Should have thrown ApiError");
            } catch (err) {
              expect(err).toBeInstanceOf(ApiError);
              const apiErr = err as ApiError;
              expect(apiErr.status).toBe(status);
              expect(apiErr.detail).toEqual(errorBody);
            }
          }
        ),
        { numRuns: 10 }
      );
    });
  });

  /**
   * Property 5: Server error toast
   * For any 5xx, a toast notification is triggered
   *
   * **Validates: Requirements 10.5**
   */
  describe("Property 5: Server error toast", () => {
    it("triggers toast notification for any 5xx status code", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.integer({ min: 500, max: 599 }),
          async (status) => {
            mockFetch.mockReset();
            const toastHandler = vi.fn();
            setToastHandler(toastHandler);

            mockGetAccessToken.mockReturnValue("valid-token");
            mockFetch.mockResolvedValueOnce(
              makeResponse(status, { error: "Server error" })
            );

            try {
              await apiGet("/test");
              expect.fail("Should have thrown ApiError");
            } catch (err) {
              expect(err).toBeInstanceOf(ApiError);
              const apiErr = err as ApiError;
              expect(apiErr.status).toBe(status);
            }

            // Verify toast was called with error type
            expect(toastHandler).toHaveBeenCalledTimes(1);
            expect(toastHandler).toHaveBeenCalledWith(
              expect.any(String),
              "error"
            );
          }
        ),
        { numRuns: 10 }
      );
    });
  });
});
