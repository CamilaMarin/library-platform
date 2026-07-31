import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useReadingProgress } from "@/lib/use-reading-progress";

// Mock api-client
const mockApiGet = vi.fn();
const mockApiPut = vi.fn();

vi.mock("@/lib/api-client", () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
  ApiError: class ApiError extends Error {
    status: number;
    detail: string;
    constructor(status: number, detail: string) {
      super(detail);
      this.name = "ApiError";
      this.status = status;
      this.detail = detail;
    }
  },
}));

describe("useReadingProgress", () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiPut.mockReset();
  });

  it("fetches progress on mount and sets loading to false", async () => {
    const progressData = {
      position: "10",
      percentage: 0.25,
      file_format: "pdf",
      last_read_at: "2024-01-01T00:00:00Z",
    };
    mockApiGet.mockResolvedValue(progressData);

    const { result } = renderHook(() => useReadingProgress("copy-123"));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApiGet).toHaveBeenCalledWith("/copies/copy-123/progress");
    expect(result.current.currentProgress).toEqual(progressData);
  });

  it("handles 404 (no existing progress) gracefully", async () => {
    const { ApiError } = await import("@/lib/api-client");
    mockApiGet.mockRejectedValue(new ApiError(404, "Not found"));

    const { result } = renderHook(() => useReadingProgress("copy-456"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.currentProgress).toBeNull();
  });

  it("saveProgress calls PUT with correct payload", async () => {
    const { ApiError } = await import("@/lib/api-client");
    mockApiGet.mockRejectedValue(new ApiError(404, "Not found"));

    const savedData = {
      position: "5",
      percentage: 0.5,
      file_format: "pdf",
      last_read_at: "2024-01-01T00:01:00Z",
    };
    mockApiPut.mockResolvedValue(savedData);

    const { result } = renderHook(() => useReadingProgress("copy-789"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.saveProgress("5", 0.5, "pdf");
    });

    await waitFor(() => {
      expect(mockApiPut).toHaveBeenCalledWith("/copies/copy-789/progress", {
        position: "5",
        percentage: 0.5,
        file_format: "pdf",
      });
    });

    await waitFor(() => {
      expect(result.current.currentProgress).toEqual(savedData);
    });
  });

  it("exposes the correct return shape", async () => {
    const { ApiError } = await import("@/lib/api-client");
    mockApiGet.mockRejectedValue(new ApiError(404, "Not found"));

    const { result } = renderHook(() => useReadingProgress("copy-shape"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current).toHaveProperty("currentProgress");
    expect(result.current).toHaveProperty("saveProgress");
    expect(result.current).toHaveProperty("loading");
    expect(typeof result.current.saveProgress).toBe("function");
  });
});
