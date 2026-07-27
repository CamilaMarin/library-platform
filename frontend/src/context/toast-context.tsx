"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { setToastHandler } from "@/lib/api-client";

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastContextValue {
  toasts: Toast[];
  showToast(message: string, type: Toast["type"]): void;
  dismissToast(id: string): void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(
    new Map()
  );

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const showToast = useCallback(
    (message: string, type: Toast["type"]) => {
      const id = crypto.randomUUID();
      const toast: Toast = { id, message, type };
      setToasts((prev) => [...prev, toast]);

      const timer = setTimeout(() => {
        dismissToast(id);
      }, 4000);
      timersRef.current.set(id, timer);
    },
    [dismissToast]
  );

  // Register the toast handler for the API client on mount
  useEffect(() => {
    setToastHandler((message, type) => {
      showToast(message, type);
    });
  }, [showToast]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer));
      timersRef.current.clear();
    };
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast debe usarse dentro de un ToastProvider");
  }
  return context;
}
