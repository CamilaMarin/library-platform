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

  // Export state
  const [exportStatus, setExportStatus] = useState<ExportStatus>("idle");
  const [exportError, setExportError] = useState<string | null>(null);

  // Delete account state
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
      if (err instanceof Error) {
        setExportError(err.message || "No se pudo exportar los datos. Intenta de nuevo más tarde.");
      } else {
        setExportError("No se pudo exportar los datos. Intenta de nuevo más tarde.");
      }
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
      if (err instanceof Error) {
        setDeleteError(err.message || "No se pudo eliminar la cuenta. Intenta de nuevo más tarde.");
      } else {
        setDeleteError("No se pudo eliminar la cuenta. Intenta de nuevo más tarde.");
      }
    }
  }

  return (
    <ProtectedRoute>
      <Navigation />
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 py-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-8">
            Configuración
          </h1>

          {/* Export Data Section */}
          <section className="mb-8 rounded-lg bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Exportar mis datos
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              De acuerdo con tus derechos ARCO (Ley 21.719), puedes solicitar
              una copia de todos los datos personales que almacenamos sobre ti.
            </p>

            <button
              type="button"
              onClick={handleExport}
              disabled={exportStatus === "loading"}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {exportStatus === "loading" ? "Exportando..." : "Exportar datos"}
            </button>

            {exportStatus === "success" && (
              <p className="mt-3 text-sm text-green-700" role="status">
                Tu exportación se está preparando. Recibirás los datos en breve.
              </p>
            )}

            {exportStatus === "error" && exportError && (
              <p className="mt-3 text-sm text-red-600" role="alert">
                {exportError}
              </p>
            )}
          </section>

          {/* Delete Account Section */}
          <section className="rounded-lg bg-white p-6 shadow-sm border-2 border-red-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Eliminar mi cuenta
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Esta acción es irreversible. Se eliminarán permanentemente todos
              tus datos personales, libros, reseñas y membresías de grupos.
            </p>

            {!showDeleteConfirm ? (
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
              >
                Eliminar cuenta
              </button>
            ) : (
              <div className="mt-4 rounded-md border border-red-300 bg-red-50 p-4">
                <p className="text-sm font-medium text-red-800 mb-3">
                  Para confirmar, escribe tu correo electrónico:{" "}
                  <span className="font-mono">{user?.email}</span>
                </p>

                <input
                  type="email"
                  value={deleteEmailInput}
                  onChange={(e) => setDeleteEmailInput(e.target.value)}
                  placeholder="tu@correo.com"
                  aria-label="Confirmar correo electrónico"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />

                <div className="mt-4 flex gap-3">
                  <button
                    type="button"
                    onClick={handleDeleteAccount}
                    disabled={!emailMatches || deleting}
                    className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
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
                    className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-1"
                  >
                    Cancelar
                  </button>
                </div>

                {deleteError && (
                  <p className="mt-3 text-sm text-red-600" role="alert">
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
