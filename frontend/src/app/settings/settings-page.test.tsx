/**
 * Integration tests for the Settings page (ARCO Profile Panel)
 *
 * Tests cover:
 * - Profile section display (Req 1.1)
 * - Rectification happy path (Req 1.2–1.4)
 * - Rectification 409 error — email already taken (Req 1.5)
 * - Export happy path (Req 2.1–2.2)
 * - Export error with retry (Req 2.4)
 * - Opposition form happy path (Req 3.1–3.4)
 * - Validation prevents submission with empty name (Req 1.8)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// ============================================================
// Mocks — must be declared before dynamic imports
// ============================================================

const mockApiGet = vi.fn();
const mockApiPatch = vi.fn();
const mockApiPost = vi.fn();
const mockApiDelete = vi.fn();

vi.mock("@/lib/api-client", () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
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

const mockTriggerJsonDownload = vi.fn();
const mockGenerateExportFilename = vi.fn(() => "entrelineas-datos-2024-01-15.json");

vi.mock("@/lib/export-download", () => ({
  triggerJsonDownload: (...args: unknown[]) => mockTriggerJsonDownload(...args),
  generateExportFilename: () => mockGenerateExportFilename(),
}));

const mockUpdateUser = vi.fn();
const mockShowToast = vi.fn();

const fakeUser = { id: "u1", name: "Ana", email: "ana@test.com" };

vi.mock("@/context/auth-context", () => ({
  useAuth: () => ({
    user: fakeUser,
    isAuthenticated: true,
    isLoading: false,
    updateUser: mockUpdateUser,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("@/context/toast-context", () => ({
  useToast: () => ({
    showToast: mockShowToast,
    toasts: [],
    dismissToast: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/settings",
  useSearchParams: () => new URLSearchParams(),
}));

// Passthrough mocks for layout components
vi.mock("@/components/protected-route", () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/navigation", () => ({
  Navigation: () => <nav data-testid="navigation" />,
}));

vi.mock("@/lib/token-storage", () => ({
  clearTokens: vi.fn(),
  getAccessToken: vi.fn(() => "mock-token"),
  getRefreshToken: vi.fn(() => "mock-refresh"),
  setTokens: vi.fn(),
}));

// Import after mocks
import SettingsPage from "./page";
import { ApiError } from "@/lib/api-client";

// ============================================================
// Helpers
// ============================================================

function renderSettingsPage() {
  return render(<SettingsPage />);
}

// ============================================================
// Tests
// ============================================================

describe("Settings Page — Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGenerateExportFilename.mockReturnValue("entrelineas-datos-2024-01-15.json");
  });

  // ----------------------------------------------------------
  // 1. Profile section renders current user data
  // ----------------------------------------------------------
  describe("Profile section display", () => {
    it("renders user name and email in display mode", () => {
      renderSettingsPage();

      expect(screen.getByText("Ana")).toBeInTheDocument();
      expect(screen.getByText("ana@test.com")).toBeInTheDocument();
    });

    it("shows the edit profile button in display mode", () => {
      renderSettingsPage();

      expect(screen.getByRole("button", { name: /editar perfil/i })).toBeInTheDocument();
    });
  });

  // ----------------------------------------------------------
  // 2. Rectification happy path
  // ----------------------------------------------------------
  describe("Rectification — happy path", () => {
    it("opens form with pre-filled values when clicking Editar perfil", async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await user.click(screen.getByRole("button", { name: /editar perfil/i }));

      const nameInput = screen.getByRole("textbox", { name: /nombre/i });
      const emailInput = screen.getByRole("textbox", { name: /correo electrónico/i });

      expect(nameInput).toHaveValue("Ana");
      expect(emailInput).toHaveValue("ana@test.com");
    });

    it("calls apiPatch with updated name, calls updateUser, shows success toast, returns to display mode", async () => {
      const user = userEvent.setup();

      mockApiPatch.mockResolvedValueOnce({
        user_id: "u1",
        name: "Ana Updated",
        email: "ana@test.com",
      });

      renderSettingsPage();

      // Enter edit mode
      await user.click(screen.getByRole("button", { name: /editar perfil/i }));

      // Update name field
      const nameInput = screen.getByRole("textbox", { name: /nombre/i });
      await user.clear(nameInput);
      await user.type(nameInput, "Ana Updated");

      // Submit
      await user.click(screen.getByRole("button", { name: /guardar/i }));

      await waitFor(() => {
        expect(mockApiPatch).toHaveBeenCalledWith("/users/me", { name: "Ana Updated" });
      });

      expect(mockUpdateUser).toHaveBeenCalledWith({
        name: "Ana Updated",
        email: "ana@test.com",
      });

      expect(mockShowToast).toHaveBeenCalledWith(
        "Perfil actualizado correctamente",
        "success"
      );

      // Should return to display mode — edit button visible again
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /editar perfil/i })).toBeInTheDocument();
      });
    });
  });

  // ----------------------------------------------------------
  // 3. Rectification — 409 error (email already taken)
  // ----------------------------------------------------------
  describe("Rectification — 409 error", () => {
    it("shows inline email error when backend returns 409", async () => {
      const user = userEvent.setup();

      mockApiPatch.mockRejectedValueOnce(
        new ApiError(409, "email_already_taken")
      );

      renderSettingsPage();

      // Enter edit mode
      await user.click(screen.getByRole("button", { name: /editar perfil/i }));

      // Change email
      const emailInput = screen.getByRole("textbox", { name: /correo electrónico/i });
      await user.clear(emailInput);
      await user.type(emailInput, "taken@test.com");

      // Submit
      await user.click(screen.getByRole("button", { name: /guardar/i }));

      await waitFor(() => {
        expect(screen.getByText(/este correo ya está en uso/i)).toBeInTheDocument();
      });

      // Toast should NOT be shown for known 409
      expect(mockShowToast).not.toHaveBeenCalled();
    });
  });

  // ----------------------------------------------------------
  // 4. Export happy path
  // ----------------------------------------------------------
  describe("Export — happy path", () => {
    it("calls apiGet and triggerJsonDownload when clicking Exportar datos", async () => {
      const user = userEvent.setup();

      const exportPayload = {
        user: { name: "Ana", email: "ana@test.com", created_at: "2024-01-01" },
        consents: [],
        memberships: [],
        processing_records: [],
      };

      mockApiGet.mockResolvedValueOnce(exportPayload);

      renderSettingsPage();

      await user.click(screen.getByRole("button", { name: /exportar datos/i }));

      await waitFor(() => {
        expect(mockApiGet).toHaveBeenCalledWith("/users/me/export");
      });

      expect(mockTriggerJsonDownload).toHaveBeenCalledWith(
        exportPayload,
        "entrelineas-datos-2024-01-15.json"
      );
    });
  });

  // ----------------------------------------------------------
  // 5. Export error with retry
  // ----------------------------------------------------------
  describe("Export — error recovery", () => {
    it("shows inline error with Reintentar button when export fails", async () => {
      const user = userEvent.setup();

      mockApiGet.mockRejectedValueOnce(new Error("Network error"));

      renderSettingsPage();

      await user.click(screen.getByRole("button", { name: /exportar datos/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
      });
    });

    it("retries the export when clicking Reintentar", async () => {
      const user = userEvent.setup();

      const exportPayload = {
        user: { name: "Ana", email: "ana@test.com", created_at: "2024-01-01" },
        consents: [],
        memberships: [],
        processing_records: [],
      };

      // First call fails, second succeeds
      mockApiGet
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce(exportPayload);

      renderSettingsPage();

      await user.click(screen.getByRole("button", { name: /exportar datos/i }));

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
      });

      // Retry
      await user.click(screen.getByRole("button", { name: /reintentar/i }));

      await waitFor(() => {
        expect(mockTriggerJsonDownload).toHaveBeenCalledWith(
          exportPayload,
          "entrelineas-datos-2024-01-15.json"
        );
      });
    });
  });

  // ----------------------------------------------------------
  // 6. Opposition form happy path
  // ----------------------------------------------------------
  describe("Opposition form — happy path", () => {
    it("opens form, selects predefined purpose, submits, shows confirmation", async () => {
      const user = userEvent.setup();

      mockApiPost.mockResolvedValueOnce({
        user_id: "u1",
        processing_purpose: "Estadísticas de uso",
        opposed: true,
      });

      renderSettingsPage();

      // Open the form
      await user.click(screen.getByRole("button", { name: /registrar oposición/i }));

      // Select predefined chip
      await user.click(screen.getByRole("button", { name: /estadísticas de uso/i }));

      // Submit
      await user.click(screen.getByRole("button", { name: /enviar oposición/i }));

      await waitFor(() => {
        expect(mockApiPost).toHaveBeenCalledWith("/users/me/oppose", {
          purpose: "Estadísticas de uso",
        });
      });

      // Confirmation message appears
      await waitFor(() => {
        expect(
          screen.getByText(/tu oposición ha sido registrada/i)
        ).toBeInTheDocument();
      });
    });
  });

  // ----------------------------------------------------------
  // 7. Validation prevents submission with empty name
  // ----------------------------------------------------------
  describe("Validation — prevents submission with empty name", () => {
    it("shows error message and disables submit when name is empty", async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      // Enter edit mode
      await user.click(screen.getByRole("button", { name: /editar perfil/i }));

      // Clear the name field and blur to trigger validation
      const nameInput = screen.getByRole("textbox", { name: /nombre/i });
      await user.clear(nameInput);
      await user.tab(); // triggers onBlur

      await waitFor(() => {
        // An error message should appear
        const alerts = screen.getAllByRole("alert");
        const nameAlert = alerts.find((el) =>
          el.textContent?.toLowerCase().includes("nombre") ||
          el.textContent?.toLowerCase().includes("requerido") ||
          el.textContent?.toLowerCase().includes("ingresa") ||
          el.textContent?.toLowerCase().includes("campo") ||
          el.textContent?.toLowerCase().includes("vacío") ||
          el.textContent?.toLowerCase().includes("obligatorio")
        );
        expect(nameAlert).toBeTruthy();
      });

      // Submit button should be disabled because form is invalid
      const submitButton = screen.getByRole("button", { name: /guardar/i });
      expect(submitButton).toBeDisabled();
    });
  });
});
