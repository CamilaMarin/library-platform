/**
 * Regression test: delete account flow
 *
 * Verifies the delete account flow still works correctly after the Settings page
 * was refactored into ProfileSection + ArcoSection components.
 *
 * Validates: Requirements 4.5
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// ── Mocks ──────────────────────────────────────────────────────────────────────

// Mock api-client
vi.mock("@/lib/api-client", () => ({
  apiDelete: vi.fn(),
  apiGet: vi.fn(),
  apiPatch: vi.fn(),
  apiPost: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    detail: string | Record<string, string>;
    constructor(status: number, detail: string | Record<string, string>) {
      super(typeof detail === "string" ? detail : JSON.stringify(detail));
      this.name = "ApiError";
      this.status = status;
      this.detail = detail;
    }
  },
}));

// Mock token-storage
vi.mock("@/lib/token-storage", () => ({
  clearTokens: vi.fn(),
  getAccessToken: vi.fn(() => null),
  getRefreshToken: vi.fn(() => null),
  setTokens: vi.fn(),
  decodeTokenPayload: vi.fn(() => null),
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/settings",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock ProtectedRoute as a passthrough
vi.mock("@/components/protected-route", () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock Navigation as a passthrough
vi.mock("@/components/navigation", () => ({
  Navigation: () => null,
}));

// Spies shared across tests
const mockUpdateUser = vi.fn();
const mockShowToast = vi.fn();

// Mock auth-context
vi.mock("@/context/auth-context", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isLoading: false,
    user: { id: "u1", name: "Ana", email: "ana@test.com" },
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateUser: mockUpdateUser,
  }),
}));

// Mock toast-context
vi.mock("@/context/toast-context", () => ({
  useToast: () => ({
    toasts: [],
    showToast: mockShowToast,
    dismissToast: vi.fn(),
  }),
}));

// Mock export-download utilities (not relevant to delete tests)
vi.mock("@/lib/export-download", () => ({
  triggerJsonDownload: vi.fn(),
  generateExportFilename: vi.fn(() => "entrelineas-datos-2025-01-01.json"),
}));

// Mock settings-validation (not relevant to delete tests)
vi.mock("@/lib/settings-validation", () => ({
  validateName: vi.fn(() => null),
  validateEmail: vi.fn(() => null),
  validatePurpose: vi.fn(() => null),
  isRectificationFormValid: vi.fn(() => true),
  isOppositionFormValid: vi.fn(() => false),
}));

// ── Import after mocks ─────────────────────────────────────────────────────────

import { apiDelete } from "@/lib/api-client";
import { clearTokens } from "@/lib/token-storage";
import SettingsPage from "./page";

// ── window.location mock ────────────────────────────────────────────────────────

let hrefSetter: ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.clearAllMocks();

  hrefSetter = vi.fn();
  Object.defineProperty(window, "location", {
    value: { ...window.location },
    writable: true,
    configurable: true,
  });
  Object.defineProperty(window.location, "href", {
    set: hrefSetter as (v: string) => void,
    get: () => "http://localhost:3000/settings",
    configurable: true,
  });

  localStorage.clear();
});

afterEach(() => {
  localStorage.clear();
});

// ── Helpers ────────────────────────────────────────────────────────────────────

function renderPage() {
  return render(<SettingsPage />);
}

/** Click the "Eliminar cuenta" button to reveal the confirmation form. */
async function openDeleteConfirm() {
  const deleteBtn = screen.getByRole("button", { name: /Eliminar cuenta/i });
  await userEvent.click(deleteBtn);
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("Settings page — delete account regression (task 9.2)", () => {
  describe("1. Delete account button visibility", () => {
    it('renders the "Eliminar cuenta" button', () => {
      renderPage();
      expect(
        screen.getByRole("button", { name: /Eliminar cuenta/i })
      ).toBeInTheDocument();
    });
  });

  describe("2. Confirmation form appears on click", () => {
    it('shows the email confirmation input when "Eliminar cuenta" is clicked', async () => {
      renderPage();
      await openDeleteConfirm();

      expect(
        screen.getByRole("textbox", { name: /Confirmar correo electrónico/i })
      ).toBeInTheDocument();
    });

    it('shows the "Confirmar eliminación" confirm button after opening', async () => {
      renderPage();
      await openDeleteConfirm();

      expect(
        screen.getByRole("button", { name: /Confirmar eliminación/i })
      ).toBeInTheDocument();
    });
  });

  describe("3. Confirm button disabled until email matches", () => {
    it("keeps confirm button disabled when typed email does not match", async () => {
      renderPage();
      await openDeleteConfirm();

      const emailInput = screen.getByRole("textbox", {
        name: /Confirmar correo electrónico/i,
      });
      await userEvent.type(emailInput, "wrong@test.com");

      const confirmBtn = screen.getByRole("button", { name: /Confirmar eliminación/i });
      expect(confirmBtn).toBeDisabled();
    });

    it("enables confirm button when typed email exactly matches user email", async () => {
      renderPage();
      await openDeleteConfirm();

      const emailInput = screen.getByRole("textbox", {
        name: /Confirmar correo electrónico/i,
      });
      await userEvent.type(emailInput, "ana@test.com");

      const confirmBtn = screen.getByRole("button", { name: /Confirmar eliminación/i });
      expect(confirmBtn).not.toBeDisabled();
    });

    it("keeps confirm button disabled when input is empty", async () => {
      renderPage();
      await openDeleteConfirm();

      const confirmBtn = screen.getByRole("button", { name: /Confirmar eliminación/i });
      expect(confirmBtn).toBeDisabled();
    });
  });

  describe("4. Happy path: delete account succeeds", () => {
    it("calls apiDelete, clearTokens, removes user_info, and redirects on success", async () => {
      vi.mocked(apiDelete).mockResolvedValueOnce(undefined);
      localStorage.setItem("user_info", JSON.stringify({ id: "u1", name: "Ana", email: "ana@test.com" }));

      renderPage();
      await openDeleteConfirm();

      const emailInput = screen.getByRole("textbox", {
        name: /Confirmar correo electrónico/i,
      });
      await userEvent.type(emailInput, "ana@test.com");

      const confirmBtn = screen.getByRole("button", { name: /Confirmar eliminación/i });
      await userEvent.click(confirmBtn);

      await waitFor(() => {
        expect(vi.mocked(apiDelete)).toHaveBeenCalledWith("/users/me");
      });

      expect(vi.mocked(clearTokens)).toHaveBeenCalled();
      expect(localStorage.getItem("user_info")).toBeNull();
      expect(hrefSetter).toHaveBeenCalledWith("/login?deleted=true");
    });
  });

  describe("5. Error path: delete API fails", () => {
    it("shows error message and re-enables button when apiDelete rejects", async () => {
      vi.mocked(apiDelete).mockRejectedValueOnce(
        new Error("No se pudo eliminar la cuenta. Intenta de nuevo más tarde.")
      );

      renderPage();
      await openDeleteConfirm();

      const emailInput = screen.getByRole("textbox", {
        name: /Confirmar correo electrónico/i,
      });
      await userEvent.type(emailInput, "ana@test.com");

      const confirmBtn = screen.getByRole("button", { name: /Confirmar eliminación/i });
      await userEvent.click(confirmBtn);

      await waitFor(() => {
        expect(
          screen.getByRole("alert")
        ).toBeInTheDocument();
      });

      // Button should be re-enabled (not stuck in loading state)
      expect(screen.getByRole("button", { name: /Confirmar eliminación/i })).not.toBeDisabled();

      // Redirect should NOT have happened
      expect(hrefSetter).not.toHaveBeenCalledWith("/login?deleted=true");
    });

    it("does not call clearTokens when delete fails", async () => {
      vi.mocked(apiDelete).mockRejectedValueOnce(new Error("Server error"));

      renderPage();
      await openDeleteConfirm();

      const emailInput = screen.getByRole("textbox", {
        name: /Confirmar correo electrónico/i,
      });
      await userEvent.type(emailInput, "ana@test.com");

      await userEvent.click(screen.getByRole("button", { name: /Confirmar eliminación/i }));

      await waitFor(() => {
        expect(screen.getByRole("alert")).toBeInTheDocument();
      });

      expect(vi.mocked(clearTokens)).not.toHaveBeenCalled();
    });
  });

  describe("6. Cancel hides the confirmation form", () => {
    it('clicking "Cancelar" hides the confirmation form', async () => {
      renderPage();
      await openDeleteConfirm();

      // Confirm form is visible
      expect(
        screen.getByRole("textbox", { name: /Confirmar correo electrónico/i })
      ).toBeInTheDocument();

      const cancelBtn = screen.getByRole("button", { name: /^Cancelar$/i });
      await userEvent.click(cancelBtn);

      // Confirm form should be gone
      expect(
        screen.queryByRole("textbox", { name: /Confirmar correo electrónico/i })
      ).not.toBeInTheDocument();
    });

    it('shows "Eliminar cuenta" button again after cancelling', async () => {
      renderPage();
      await openDeleteConfirm();

      const cancelBtn = screen.getByRole("button", { name: /^Cancelar$/i });
      await userEvent.click(cancelBtn);

      expect(
        screen.getByRole("button", { name: /Eliminar cuenta/i })
      ).toBeInTheDocument();
    });
  });
});
