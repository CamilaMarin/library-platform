import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ToastProvider, useToast } from "./toast-context";

function wrapper({ children }: { children: React.ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>;
}

describe("Toast Context", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("showToast adds a toast to the list", () => {
    const { result } = renderHook(() => useToast(), { wrapper });

    act(() => {
      result.current.showToast("Libro agregado", "success");
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].message).toBe("Libro agregado");
    expect(result.current.toasts[0].type).toBe("success");
  });

  it("supports success, error, and info types", () => {
    const { result } = renderHook(() => useToast(), { wrapper });

    act(() => {
      result.current.showToast("Éxito", "success");
      result.current.showToast("Error", "error");
      result.current.showToast("Info", "info");
    });

    expect(result.current.toasts).toHaveLength(3);
    expect(result.current.toasts[0].type).toBe("success");
    expect(result.current.toasts[1].type).toBe("error");
    expect(result.current.toasts[2].type).toBe("info");
  });

  it("auto-dismisses toast after 4 seconds", () => {
    const { result } = renderHook(() => useToast(), { wrapper });

    act(() => {
      result.current.showToast("Temporal", "info");
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      vi.advanceTimersByTime(4000);
    });

    expect(result.current.toasts).toHaveLength(0);
  });

  it("dismissToast removes a specific toast immediately", () => {
    const { result } = renderHook(() => useToast(), { wrapper });

    act(() => {
      result.current.showToast("Primera", "success");
      result.current.showToast("Segunda", "error");
    });

    expect(result.current.toasts).toHaveLength(2);

    act(() => {
      result.current.dismissToast(result.current.toasts[0].id);
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].message).toBe("Segunda");
  });

  it("throws error when useToast is used outside ToastProvider", () => {
    expect(() => {
      renderHook(() => useToast());
    }).toThrow("useToast debe usarse dentro de un ToastProvider");
  });

  it("stacks multiple toasts", () => {
    const { result } = renderHook(() => useToast(), { wrapper });

    act(() => {
      result.current.showToast("Toast 1", "success");
      result.current.showToast("Toast 2", "error");
      result.current.showToast("Toast 3", "info");
    });

    expect(result.current.toasts).toHaveLength(3);
  });

  it("each toast has a unique id", () => {
    const { result } = renderHook(() => useToast(), { wrapper });

    act(() => {
      result.current.showToast("A", "success");
      result.current.showToast("B", "success");
    });

    const ids = result.current.toasts.map((t) => t.id);
    expect(new Set(ids).size).toBe(2);
  });
});
