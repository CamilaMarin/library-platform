import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { PdfReader } from "@/components/pdf-reader";

// Mock pdfjs-dist
vi.mock("pdfjs-dist", () => ({
  GlobalWorkerOptions: { workerSrc: "" },
  getDocument: vi.fn(),
}));

// Mock use-reading-progress hook
const mockSaveProgress = vi.fn();
vi.mock("@/lib/use-reading-progress", () => ({
  useReadingProgress: () => ({
    currentProgress: null,
    saveProgress: mockSaveProgress,
    loading: false,
  }),
}));

// Mock token-storage
vi.mock("@/lib/token-storage", () => ({
  getAccessToken: () => "fake-token",
}));

describe("PdfReader", () => {
  beforeEach(() => {
    mockSaveProgress.mockReset();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("shows loading state while PDF is being fetched", () => {
    // Fetch never resolves — stays in loading
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise(() => {})
    );

    render(
      <PdfReader copyId="copy-1" fileUrl="/copies/copy-1/file" onClose={vi.fn()} />
    );

    expect(screen.getByText("Cargando documento...")).toBeInTheDocument();
  });

  it("shows error state on 403 response", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 403,
    });

    render(
      <PdfReader copyId="copy-1" fileUrl="/copies/copy-1/file" onClose={vi.fn()} />
    );

    expect(
      await screen.findByText("No tienes permiso para acceder a este archivo.")
    ).toBeInTheDocument();
  });

  it("shows generic error for non-403 failures", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 500,
    });

    render(
      <PdfReader copyId="copy-1" fileUrl="/copies/copy-1/file" onClose={vi.fn()} />
    );

    expect(
      await screen.findByText("Error al cargar el archivo (500).")
    ).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked in error state", async () => {
    const onClose = vi.fn();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 403,
    });

    render(
      <PdfReader copyId="copy-1" fileUrl="/copies/copy-1/file" onClose={onClose} />
    );

    const closeButton = await screen.findByText("Cerrar");
    closeButton.click();

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
