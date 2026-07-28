"use client";

import { useToast } from "@/context/toast-context";

// Colores semánticos que respetan la identidad — sin romper legibilidad
const typeStyles: Record<string, React.CSSProperties> = {
  success: { background: "var(--color-reading)", color: "var(--color-cream)" },
  error:   { background: "var(--color-leather)", color: "var(--color-cream)" },
  info:    { background: "var(--color-walnut)",  color: "var(--color-parchment)" },
};

const typeIcons: Record<string, string> = {
  success: "✓",
  error:   "✕",
  info:    "ℹ",
};

export function ToastContainer() {
  const { toasts, dismissToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="fixed bottom-4 left-1/2 z-50 flex -translate-x-1/2 flex-col gap-2 md:left-auto md:right-4 md:translate-x-0"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="alert"
          className="flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg transition-all duration-300"
          style={typeStyles[toast.type]}
        >
          <span className="text-lg" aria-hidden="true">
            {typeIcons[toast.type]}
          </span>
          <p className="text-sm font-medium">{toast.message}</p>
          <button
            onClick={() => dismissToast(toast.id)}
            className="ml-2 rounded p-1 opacity-80 transition-opacity hover:opacity-100 focus:outline-none"
            aria-label="Cerrar notificación"
          >
            <span aria-hidden="true">✕</span>
          </button>
        </div>
      ))}
    </div>
  );
}
