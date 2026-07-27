import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import * as fc from "fast-check";

// === Mocks ===

const mockReplace = vi.fn();
const mockPush = vi.fn();
const mockRouter = {
  replace: mockReplace,
  push: mockPush,
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  prefetch: vi.fn(),
};

let mockPathname = "/dashboard";
let mockAuthState = {
  isAuthenticated: false,
  isLoading: false,
  user: null,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
};

vi.mock("next/navigation", () => ({
  useRouter: () => mockRouter,
  usePathname: () => mockPathname,
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/context/auth-context", () => ({
  useAuth: () => mockAuthState,
}));

// Import after mocks are set up
import { ProtectedRoute } from "@/components/protected-route";

describe("ProtectedRoute Property Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthState = {
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    };
  });

  /**
   * Property 6: Protected route redirect with destination preservation
   * For any path not `/login` or `/register`, unauthenticated users redirect
   * to `/login?redirect={originalPath}`
   *
   * **Validates: Requirements 2.1, 2.2**
   */
  describe("Property 6: Protected route redirect with destination preservation", () => {
    it("redirects unauthenticated users to /login?redirect={path} for any protected path", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc
            .webPath()
            .filter(
              (p) =>
                p.length > 0 &&
                p !== "/login" &&
                p !== "/register" &&
                !p.startsWith("/login/") &&
                !p.startsWith("/register/")
            ),
          async (path) => {
            vi.clearAllMocks();

            // Ensure path starts with /
            const normalizedPath = path.startsWith("/") ? path : `/${path}`;

            mockPathname = normalizedPath;
            mockAuthState = {
              isAuthenticated: false,
              isLoading: false,
              user: null,
              login: vi.fn(),
              register: vi.fn(),
              logout: vi.fn(),
            };

            const { unmount } = render(
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            );

            // Wait for useEffect to run
            await vi.waitFor(() => {
              expect(mockReplace).toHaveBeenCalled();
            });

            const expectedRedirect = `/login?redirect=${encodeURIComponent(normalizedPath)}`;
            expect(mockReplace).toHaveBeenCalledWith(expectedRedirect);

            unmount();
          }
        ),
        { numRuns: 10 }
      );
    });

    it("does not render children when unauthenticated", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc
            .webPath()
            .filter((p) => p.length > 0 && p !== "/login" && p !== "/register"),
          async (path) => {
            vi.clearAllMocks();

            const normalizedPath = path.startsWith("/") ? path : `/${path}`;
            mockPathname = normalizedPath;
            mockAuthState = {
              isAuthenticated: false,
              isLoading: false,
              user: null,
              login: vi.fn(),
              register: vi.fn(),
              logout: vi.fn(),
            };

            const { queryByText, unmount } = render(
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            );

            expect(queryByText("Protected Content")).not.toBeInTheDocument();

            unmount();
          }
        ),
        { numRuns: 10 }
      );
    });
  });

  /**
   * Property 7: Post-login redirect consumption
   * For any valid redirect param, after auth the user navigates to that stored path
   *
   * **Validates: Requirements 2.3**
   *
   * NOTE: This property tests that when a user is authenticated,
   * the ProtectedRoute renders children (allowing the login page to consume
   * the redirect param). The full redirect consumption is handled by the Login
   * page (task 5.1). Here we verify the ProtectedRoute allows rendering when
   * authenticated, which is the prerequisite for redirect consumption.
   */
  describe("Property 7: Post-login redirect consumption", () => {
    it("renders children for authenticated users regardless of path (enabling redirect consumption)", async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.webPath().filter((p) => p.length > 0),
          async (path) => {
            vi.clearAllMocks();

            const normalizedPath = path.startsWith("/") ? path : `/${path}`;
            mockPathname = normalizedPath;
            mockAuthState = {
              isAuthenticated: true,
              isLoading: false,
              user: { id: "user-1", name: "Test User", email: "test@example.com" },
              login: vi.fn(),
              register: vi.fn(),
              logout: vi.fn(),
            };

            const { getByText, unmount } = render(
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            );

            expect(getByText("Protected Content")).toBeInTheDocument();
            // Should NOT redirect when authenticated
            expect(mockReplace).not.toHaveBeenCalled();

            unmount();
          }
        ),
        { numRuns: 10 }
      );
    });

    // TODO: Full post-login redirect consumption test will be added with the Login page (task 5.1).
    // The login page reads `redirect` from useSearchParams and navigates there after successful auth.
  });
});
