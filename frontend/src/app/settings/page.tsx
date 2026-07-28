"use client";

import { useState } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { useAuth } from "@/context/auth-context";
import { apiGet, apiDelete } from "@/lib/api-client";
import { clearTokens } from "@/lib/token-storage";
import type { ExportData } from "@/types";

type ExportStatus = "idle" | "loading" | "success" | "error";

export default function SettingsPage() {
  const { user } = useAuth();

  const [exportStatus, setExportStatus] = useState<ExportStatus>("idle");
  const [exportError, setExportError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteEmailInput, setDeleteEmailInput] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const emailMatches = deleteEmailInput === user?.email;

  async function handleExport() {
    setExportStatus("loading");
    setExportError(null);
    try {
      await apiGet<ExportData>("/users/me/export");
      setExportStatus("success");
    } catch (err: unknown) {
      setExportStatus("error");
      setExportError(
        err instanceof Error
          ? err.message || "No se pudo exportar los datos. Intenta de nuevo más tarde."
          : "No se pudo exportar los datos. Intenta de nuevo más tarde."
      );
    }
  }

  async function handleDeleteAccount() {
    if (!emailMatches) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await apiDelete("/users/me");
      clearTokens();
      if (typeof window !== "undefined") {
        localStorage.removeItem("user_info");
      }
      window.location.href = "/login?deleted=true";
    } catch (err: unknown) {
      setDeleting(false);
      setDeleteError(
        err instanceof Error
          ? err.message || "No se pudo eliminar la cuenta. Intenta de nuevo más tarde."
          : "No se pudo eliminar la cuenta. Intenta de nuevo más tarde."
      );
    }
  }

  return (
    <ProtectedRoute>
      <Navigation />
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-3xl mx-auto px-4 py-8">
          <h1
            className="text-2xl font-bold mb-8"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--color-walnut)",
            }}
          >
            Configuración
          </h1>

          {/* Export Data */}
          <section
            className="mb-6 rounded-lg p-6"
            style={{
              background: "var(--color-cream)",
              border: "1px solid var(--color-border)",
              boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
            }}
          >
            <h2
              className="text-lg font-semibold mb-2"
              style={{ color: "var(--color-walnut)" }}
            >
              Exportar mis datos
            </h2>
            <p className="text-sm mb-4" style={{ color: "var(--color-ink-soft)" }}>
              De acuerdo con tus derechos ARCO (Ley 21.719), puedes solicitar
              una copia de todos los datos personales que almacenamos sobre ti.
            </p>

            <button
              type="button"
              onClick={handleExport}
              disabled={exportStatus === "loading"}
              className="rounded-full px-4 py-2 text-sm font-medium transition-colors focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
              style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
              onMouseEnter={(e) => {
                if (exportStatus !== "loading")
                  (e.currentTarget as HTMLButtonElement).style.background =
                    "var(--color-mahogany)";
              }}
              onMouseLeave={(e) => {
                if (exportStatus !== "loading")
                  (e.currentTarget as HTMLButtonElement).style.background =
                    "var(--color-walnut)";
              }}
            >
              {exportStatus === "loading" ? "Exportando..." : "Exportar datos"}
            </button>

            {exportStatus === "success" && (
              <p
                className="mt-3 text-sm"
                style={{ color: "var(--color-reading)" }}
                role="status"
              >
                Tu exportación se está preparando. Recibirás los datos en breve.
              </p>
            )}

            {exportStatus === "error" && exportError && (
              <p
                className="mt-3 text-sm"
                style={{ color: "var(--color-leather)" }}
                role="alert"
              >
                {exportError}
              </p>
            )}
          </section>

          {/* Delete Account */}
          <section
            className="rounded-lg p-6"
            style={{
              background: "var(--color-cream)",
              border: "2px solid var(--color-leather)",
              boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
            }}
          >
            <h2
              className="text-lg font-semibold mb-2"
              style={{ color: "var(--color-leather)" }}
            >
              Eliminar mi cuenta
            </h2>
            <p className="text-sm mb-4" style={{ color: "var(--color-ink-soft)" }}>
              Esta acción es irreversible. Se eliminarán permanentemente todos
              tus datos personales, libros, reseñas y membresías de grupos.
            </p>

            {!showDeleteConfirm ? (
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="rounded-full px-4 py-2 text-sm font-medium transition-colors focus:outline-none"
                style={{ background: "var(--color-leather)", color: "var(--color-cream)" }}
                onMouseEnter={(e) =>
                  ((e.currentTarget as HTMLButtonElement).style.background = "#8A3A2A")
                }
                onMouseLeave={(e) =>
                  ((e.currentTarget as HTMLButtonElement).style.background =
                    "var(--color-leather)")
                }
              >
                Eliminar cuenta
              </button>
            ) : (
              <div
                className="mt-4 rounded-md p-4"
                style={{ background: "#FAF0E8", border: "1px solid var(--color-leather)" }}
              >
                <p
                  className="text-sm font-medium mb-3"
                  style={{ color: "var(--color-leather)" }}
                >
                  Para confirmar, escribe tu correo electrónico:{" "}
                  <span className="font-mono" style={{ color: "var(--color-walnut)" }}>
                    {user?.email}
                  </span>
                </p>

                <input
                  type="email"
                  value={deleteEmailInput}
                  onChange={(e) => setDeleteEmailInput(e.target.value)}
                  placeholder="tu@correo.com"
                  aria-label="Confirmar correo electrónico"
                  className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none"
                  style={{
                    borderColor: "var(--color-leather)",
                    background: "var(--color-cream)",
                    color: "var(--color-ink)",
                  }}
                />

                <div className="mt-4 flex gap-3">
                  <button
                    type="button"
                    onClick={handleDeleteAccount}
                    disabled={!emailMatches || deleting}
                    className="rounded-full px-4 py-2 text-sm font-medium transition-colors focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                    style={{ background: "var(--color-leather)", color: "var(--color-cream)" }}
                    onMouseEnter={(e) => {
                      if (emailMatches && !deleting)
                        (e.currentTarget as HTMLButtonElement).style.background = "#8A3A2A";
                    }}
                    onMouseLeave={(e) => {
                      if (emailMatches && !deleting)
                        (e.currentTarget as HTMLButtonElement).style.background =
                          "var(--color-leather)";
                    }}
                  >
                    {deleting ? "Eliminando..." : "Confirmar eliminación"}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setShowDeleteConfirm(false);
                      setDeleteEmailInput("");
                      setDeleteError(null);
                    }}
                    className="rounded-full px-4 py-2 text-sm font-medium transition-colors focus:outline-none"
                    style={{
                      border: "1px solid var(--color-border)",
                      color: "var(--color-ink-soft)",
                      background: "transparent",
                    }}
                    onMouseEnter={(e) =>
                      ((e.currentTarget as HTMLButtonElement).style.background =
                        "var(--color-parchment)")
                    }
                    onMouseLeave={(e) =>
                      ((e.currentTarget as HTMLButtonElement).style.background =
                        "transparent")
                    }
                  >
                    Cancelar
                  </button>
                </div>

                {deleteError && (
                  <p
                    className="mt-3 text-sm"
                    style={{ color: "var(--color-leather)" }}
                    role="alert"
                  >
                    {deleteError}
                  </p>
                )}
              </div>
            )}
          </section>
        </div>
      </main>
    </ProtectedRoute>
  );
}
