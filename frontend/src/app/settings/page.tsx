"use client";

import { useState, useEffect } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { useAuth } from "@/context/auth-context";
import { apiGet, apiDelete, apiPatch, apiPost, ApiError } from "@/lib/api-client";
import { clearTokens } from "@/lib/token-storage";
import { triggerJsonDownload, generateExportFilename } from "@/lib/export-download";
import { validateName, validateEmail, isRectificationFormValid, validatePurpose, isOppositionFormValid } from "@/lib/settings-validation";
import { useToast } from "@/context/toast-context";
import type { ExportData, RectifyResponse, OpposeRequest, OpposeResponse, OppositionsResponse } from "@/types";

// ============================================================
// Types
// ============================================================

type ExportStatus = "idle" | "loading" | "error";

// ============================================================
// ProfileSection
// ============================================================

function ProfileSection() {
  const { user, updateUser } = useAuth();
  const { showToast } = useToast();

  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [nameError, setNameError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  function handleNameBlur() {
    setNameError(validateName(name));
  }

  function handleEmailBlur() {
    setEmailError(validateEmail(email));
  }

  function handleEdit() {
    // Pre-fill with current stored values
    setName(user?.name ?? "");
    setEmail(user?.email ?? "");
    setNameError(null);
    setEmailError(null);
    setIsEditing(true);
  }

  function handleCancel() {
    // Reset to current stored values and exit edit mode
    setName(user?.name ?? "");
    setEmail(user?.email ?? "");
    setNameError(null);
    setEmailError(null);
    setIsEditing(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nameErr = validateName(name);
    const emailErr = validateEmail(email);
    setNameError(nameErr);
    setEmailError(emailErr);
    if (nameErr || emailErr) return;

    setIsSubmitting(true);
    setServerError(null);

    // Build payload with only changed fields
    const payload: { name?: string; email?: string } = {};
    if (name !== user?.name) payload.name = name;
    if (email !== user?.email) payload.email = email;

    // Edge case: no changes
    if (Object.keys(payload).length === 0) {
      setIsSubmitting(false);
      setServerError("Debes modificar al menos un campo");
      return;
    }

    try {
      const response = await apiPatch<RectifyResponse>("/users/me", payload);
      updateUser({ name: response.name, email: response.email });
      setIsEditing(false);
      showToast("Perfil actualizado correctamente", "success");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        const detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
        if (err.status === 409 || detail === "email_already_taken") {
          setEmailError("Este correo ya está en uso");
        } else if (detail === "invalid_email_format") {
          setEmailError("Formato de correo inválido");
        } else if (detail === "no_fields_provided") {
          setServerError("Debes modificar al menos un campo");
        } else {
          showToast("Ocurrió un error. Intenta de nuevo.", "error");
        }
      } else {
        showToast("Ocurrió un error. Intenta de nuevo.", "error");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const formValid = isRectificationFormValid(name, email);

  return (
    <section
      className="card-biblioteca mb-6 p-6"
      aria-labelledby="profile-section-heading"
    >
      <h2
        id="profile-section-heading"
        className="text-lg font-semibold mb-4"
        style={{
          fontFamily: "var(--font-playfair), Georgia, serif",
          color: "var(--color-walnut)",
        }}
      >
        Mi perfil
      </h2>

      {!isEditing ? (
        /* ── Display mode ── */
        <div>
          <dl className="space-y-3 mb-5">
            <div>
              <dt
                className="text-xs font-medium uppercase tracking-wide mb-0.5"
                style={{ color: "var(--color-ink-faint)" }}
              >
                Nombre
              </dt>
              <dd className="text-sm font-medium" style={{ color: "var(--color-ink)" }}>
                {user?.name || <span style={{ color: "var(--color-ink-faint)" }}>—</span>}
              </dd>
            </div>
            <div>
              <dt
                className="text-xs font-medium uppercase tracking-wide mb-0.5"
                style={{ color: "var(--color-ink-faint)" }}
              >
                Correo electrónico
              </dt>
              <dd className="text-sm font-medium" style={{ color: "var(--color-ink)" }}>
                {user?.email || <span style={{ color: "var(--color-ink-faint)" }}>—</span>}
              </dd>
            </div>
          </dl>

          <button
            type="button"
            onClick={handleEdit}
            className="btn-primary focus:outline-none"
          >
            Editar perfil
          </button>
        </div>
      ) : (
        /* ── Edit mode ── */
        <form onSubmit={handleSubmit} noValidate>
          <div className="space-y-4 mb-5">
            {/* Name field */}
            <div>
              <label
                htmlFor="profile-name"
                className="block text-sm font-medium mb-1"
                style={{ color: "var(--color-ink-soft)" }}
              >
                Nombre
              </label>
              <input
                id="profile-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onBlur={handleNameBlur}
                aria-label="Nombre"
                aria-describedby={nameError ? "profile-name-error" : undefined}
                aria-invalid={!!nameError}
                className="w-full rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
                style={{
                  borderColor: nameError ? "var(--color-leather)" : "var(--color-border)",
                  background: "var(--color-cream)",
                  color: "var(--color-ink)",
                }}
              />
              {nameError && (
                <p
                  id="profile-name-error"
                  className="mt-1 text-xs"
                  role="alert"
                  style={{ color: "var(--color-leather)" }}
                >
                  {nameError}
                </p>
              )}
            </div>

            {/* Email field */}
            <div>
              <label
                htmlFor="profile-email"
                className="block text-sm font-medium mb-1"
                style={{ color: "var(--color-ink-soft)" }}
              >
                Correo electrónico
              </label>
              <input
                id="profile-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={handleEmailBlur}
                aria-label="Correo electrónico"
                aria-describedby={emailError ? "profile-email-error" : undefined}
                aria-invalid={!!emailError}
                className="w-full rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
                style={{
                  borderColor: emailError ? "var(--color-leather)" : "var(--color-border)",
                  background: "var(--color-cream)",
                  color: "var(--color-ink)",
                }}
              />
              {emailError && (
                <p
                  id="profile-email-error"
                  className="mt-1 text-xs"
                  role="alert"
                  style={{ color: "var(--color-leather)" }}
                >
                  {emailError}
                </p>
              )}
            </div>
          </div>

          <div className="flex gap-3 flex-wrap">
            <button
              type="submit"
              disabled={!formValid || isSubmitting}
              className="btn-primary focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? "Guardando..." : "Guardar"}
            </button>

            <button
              type="button"
              onClick={handleCancel}
              className="rounded-full px-5 py-2.5 text-sm font-medium transition-colors focus:outline-none"
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
                ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
              }
            >
              Cancelar
            </button>
          </div>

          {serverError && (
            <p className="mt-2 text-xs" role="alert" style={{ color: "var(--color-leather)" }}>
              {serverError}
            </p>
          )}
        </form>
      )}
    </section>
  );
}

// ============================================================
// OppositionForm — Oposición ARCO right
// ============================================================

const OPPOSITION_PURPOSES = [
  "Recomendaciones de lectura",
  "Estadísticas de uso",
  "Comunicaciones no esenciales",
] as const;

function OppositionForm() {
  const { showToast } = useToast();

  const [isOpen, setIsOpen] = useState(false);
  const [purpose, setPurpose] = useState("");
  const [purposeError, setPurposeError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [activeOppositions, setActiveOppositions] = useState<string[]>([]);
  const [loadingOppositions, setLoadingOppositions] = useState(true);

  useEffect(() => {
    apiGet<OppositionsResponse>("/users/me/oppositions")
      .then((data) => {
        setActiveOppositions(data.opposed_purposes);
      })
      .catch((err) => {
        // Silently log — do not block the main UI
        console.error("Failed to load oppositions:", err);
      })
      .finally(() => {
        setLoadingOppositions(false);
      });
  }, []);

  function handleOpen() {
    setIsOpen(true);
  }

  function handleCancel() {
    setIsOpen(false);
    setPurpose("");
    setPurposeError(null);
    setServerError(null);
  }

  function handleReset() {
    setShowConfirmation(false);
    setPurpose("");
    setPurposeError(null);
    setServerError(null);
    setIsOpen(true);
  }

  function handlePurposeBlur() {
    setPurposeError(validatePurpose(purpose));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const err = validatePurpose(purpose);
    setPurposeError(err);
    if (err) return;

    setIsSubmitting(true);
    setServerError(null);

    try {
      const payload: OpposeRequest = { purpose };
      await apiPost<OpposeResponse>("/users/me/oppose", payload);
      setActiveOppositions((prev) => [...prev, purpose]);
      setShowConfirmation(true);
      setPurpose("");
      setPurposeError(null);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
        if (err.status === 400) {
          setServerError(detail || "Solicitud inválida. Verifica el motivo ingresado.");
        } else {
          showToast("Ocurrió un error. Intenta de nuevo.", "error");
        }
      } else {
        setServerError("Ocurrió un error. Intenta de nuevo.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const formValid = isOppositionFormValid(purpose);

  return (
    <div className="card-biblioteca mb-4 p-6">
      <h3
        className="text-base font-semibold mb-1"
        style={{ color: "var(--color-walnut)" }}
      >
        Oposición — Registrar oposición
      </h3>
      <p className="text-sm mb-4" style={{ color: "var(--color-ink-soft)" }}>
        Tienes derecho a oponerte al tratamiento de tus datos personales para
        determinados fines.
      </p>

      {/* Active oppositions list */}
      {loadingOppositions ? (
        <div className="mb-4 animate-pulse bg-gray-200 h-4 rounded" aria-hidden="true" />
      ) : !loadingOppositions && activeOppositions.length === 0 ? (
        <p className="text-sm mb-4" style={{ color: "var(--color-ink-faint)" }}>
          No tienes oposiciones registradas aún.
        </p>
      ) : (
        <ul
          className="flex flex-wrap gap-2 mb-4"
          aria-label="Oposiciones registradas"
        >
          {activeOppositions.map((item) => (
            <li key={item}>
              <span
                className="rounded-full px-3 py-1 text-sm"
                style={{
                  border: "1px solid var(--color-teak)",
                  color: "var(--color-teak)",
                  background: "transparent",
                }}
              >
                {item}
              </span>
            </li>
          ))}
        </ul>
      )}

      {showConfirmation ? (
        /* ── Confirmation state ── */
        <div>
          <p
            className="text-sm mb-3"
            role="status"
            style={{ color: "var(--color-reading)" }}
          >
            Tu oposición ha sido registrada.
          </p>
          <button
            type="button"
            onClick={handleReset}
            className="rounded-full px-4 py-2 text-sm font-medium transition-colors focus:outline-none"
            style={{
              border: "1px solid var(--color-teak)",
              color: "var(--color-teak)",
              background: "transparent",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background =
                "var(--color-parchment)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
            }
          >
            Registrar otra oposición
          </button>
        </div>
      ) : !isOpen ? (
        /* ── Collapsed state ── */
        <button
          type="button"
          onClick={handleOpen}
          className="btn-primary focus:outline-none"
        >
          Registrar oposición
        </button>
      ) : (
        /* ── Form open state ── */
        <form onSubmit={handleSubmit} noValidate>
          {/* Predefined purpose chips */}
          <div className="flex flex-wrap gap-2 mb-3" aria-label="Motivos sugeridos">
            {OPPOSITION_PURPOSES.map((chip) => {
              const isSelected = purpose === chip;
              return (
                <button
                  key={chip}
                  type="button"
                  onClick={() => {
                    setPurpose(chip);
                    setPurposeError(null);
                  }}
                  className="rounded-full px-3 py-1 text-sm transition-colors focus:outline-none"
                  style={{
                    border: "1px solid var(--color-teak)",
                    background: isSelected ? "var(--color-teak)" : "transparent",
                    color: isSelected ? "var(--color-cream)" : "var(--color-teak)",
                  }}
                >
                  {chip}
                </button>
              );
            })}
          </div>

          {/* Purpose text input */}
          <div className="mb-4">
            <label
              htmlFor="opposition-purpose"
              className="block text-sm font-medium mb-1"
              style={{ color: "var(--color-ink-soft)" }}
            >
              Motivo de oposición
            </label>
            <input
              id="opposition-purpose"
              type="text"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              onBlur={handlePurposeBlur}
              aria-label="Motivo de oposición"
              aria-describedby={purposeError ? "opposition-purpose-error" : undefined}
              aria-invalid={!!purposeError}
              placeholder="Describe el motivo de tu oposición"
              className="w-full rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
              style={{
                borderColor: purposeError
                  ? "var(--color-leather)"
                  : "var(--color-border)",
                background: "var(--color-cream)",
                color: "var(--color-ink)",
              }}
            />
            {purposeError && (
              <p
                id="opposition-purpose-error"
                className="mt-1 text-xs"
                role="alert"
                style={{ color: "var(--color-leather)" }}
              >
                {purposeError}
              </p>
            )}
          </div>

          <div className="flex gap-3 flex-wrap">
            <button
              type="submit"
              disabled={!formValid || isSubmitting}
              className="btn-primary focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? "Enviando..." : "Enviar oposición"}
            </button>

            <button
              type="button"
              onClick={handleCancel}
              className="rounded-full px-5 py-2.5 text-sm font-medium transition-colors focus:outline-none"
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
                ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
              }
            >
              Cancelar
            </button>
          </div>

          {serverError && (
            <p
              className="mt-3 text-sm"
              role="alert"
              style={{ color: "var(--color-leather)" }}
            >
              {serverError}
            </p>
          )}
        </form>
      )}
    </div>
  );
}

// ============================================================
// ArcoSection — ARCO rights: Acceso, Rectificación, Cancelación, Oposición
// ============================================================

interface ArcoSectionProps {
  user: { email?: string } | null;
  exportStatus: ExportStatus;
  exportError: string | null;
  showDeleteConfirm: boolean;
  deleteEmailInput: string;
  deleting: boolean;
  deleteError: string | null;
  emailMatches: boolean;
  onExport: () => void;
  onShowDeleteConfirm: () => void;
  onDeleteAccount: () => void;
  onCancelDelete: () => void;
  onDeleteEmailChange: (value: string) => void;
}

function ArcoSection({
  user,
  exportStatus,
  exportError,
  showDeleteConfirm,
  deleteEmailInput,
  deleting,
  deleteError,
  emailMatches,
  onExport,
  onShowDeleteConfirm,
  onDeleteAccount,
  onCancelDelete,
  onDeleteEmailChange,
}: ArcoSectionProps) {
  return (
    <section aria-labelledby="arco-section-heading">
      {/* Section header */}
      <div className="mb-4">
        <h2
          id="arco-section-heading"
          className="text-lg font-semibold"
          style={{
            fontFamily: "var(--font-playfair), Georgia, serif",
            color: "var(--color-walnut)",
          }}
        >
          Derechos ARCO
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--color-ink-soft)" }}>
          De acuerdo con la Ley 21.719 de Chile, tienes derecho de Acceso,
          Rectificación, Cancelación y Oposición sobre tus datos personales.
        </p>
      </div>

      {/* Acceso — Export Data */}
      <div
        className="card-biblioteca mb-4 p-6"
      >
        <h3
          className="text-base font-semibold mb-1"
          style={{ color: "var(--color-walnut)" }}
        >
          Acceso — Exportar mis datos
        </h3>
        <p className="text-sm mb-4" style={{ color: "var(--color-ink-soft)" }}>
          Solicita una copia portable de todos los datos personales que
          almacenamos sobre ti.
        </p>

        <button
          type="button"
          onClick={onExport}
          disabled={exportStatus === "loading"}
          className="btn-primary focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          {exportStatus === "loading" ? "Exportando..." : "Exportar datos"}
        </button>

        {exportStatus === "error" && exportError && (
          <div className="mt-3">
            <p
              className="text-sm"
              style={{ color: "var(--color-leather)" }}
              role="alert"
            >
              {exportError}
            </p>
            <button
              type="button"
              onClick={onExport}
              className="mt-2 rounded-full px-4 py-2 text-sm font-medium transition-colors focus:outline-none"
              style={{
                border: "1px solid var(--color-leather)",
                color: "var(--color-leather)",
                background: "transparent",
              }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background = "#FAF0E8")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
              }
            >
              Reintentar
            </button>
          </div>
        )}
      </div>

      {/* Rectificación — Reference to Profile Section */}
      <div className="card-biblioteca mb-4 p-6">
        <h3
          className="text-base font-semibold mb-1"
          style={{ color: "var(--color-walnut)" }}
        >
          Rectificación — Editar mis datos
        </h3>
        <p className="text-sm mb-3" style={{ color: "var(--color-ink-soft)" }}>
          Puedes modificar tu nombre y correo electrónico desde la sección de
          perfil al inicio de esta página.
        </p>
        <a
          href="#profile-section-heading"
          className="text-sm font-medium focus:outline-none"
          style={{ color: "var(--color-teak)", textDecoration: "underline" }}
        >
          Ir a Mi perfil ↑
        </a>
      </div>

      {/* Oposición — Opposition Form */}
      <OppositionForm />

      {/* Cancelación — Delete Account */}
      <div
        className="rounded-lg p-6"
        style={{
          background: "var(--color-cream)",
          border: "2px solid var(--color-leather)",
          boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
        }}
      >
        <h3
          className="text-base font-semibold mb-1"
          style={{ color: "var(--color-leather)" }}
        >
          Cancelación — Eliminar mi cuenta
        </h3>
        <p className="text-sm mb-4" style={{ color: "var(--color-ink-soft)" }}>
          Esta acción es irreversible. Se eliminarán permanentemente todos tus
          datos personales, libros, reseñas y membresías de grupos.
        </p>

        {!showDeleteConfirm ? (
          <button
            type="button"
            onClick={onShowDeleteConfirm}
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
              onChange={(e) => onDeleteEmailChange(e.target.value)}
              placeholder="tu@correo.com"
              aria-label="Confirmar correo electrónico"
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none"
              style={{
                borderColor: "var(--color-leather)",
                background: "var(--color-cream)",
                color: "var(--color-ink)",
              }}
            />

            <div className="mt-4 flex gap-3 flex-wrap">
              <button
                type="button"
                onClick={onDeleteAccount}
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
                onClick={onCancelDelete}
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
                  ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
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
      </div>
    </section>
  );
}

// ============================================================
// Page
// ============================================================

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
      const data = await apiGet<ExportData>("/users/me/export");
      triggerJsonDownload(data, generateExportFilename());
      setExportStatus("idle");
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

          {/* ── Profile Section ── */}
          <ProfileSection />

          {/* ── ARCO Section ── */}
          <ArcoSection
            user={user}
            exportStatus={exportStatus}
            exportError={exportError}
            showDeleteConfirm={showDeleteConfirm}
            deleteEmailInput={deleteEmailInput}
            deleting={deleting}
            deleteError={deleteError}
            emailMatches={emailMatches}
            onExport={handleExport}
            onShowDeleteConfirm={() => setShowDeleteConfirm(true)}
            onDeleteAccount={handleDeleteAccount}
            onCancelDelete={() => {
              setShowDeleteConfirm(false);
              setDeleteEmailInput("");
              setDeleteError(null);
            }}
            onDeleteEmailChange={setDeleteEmailInput}
          />
        </div>
      </main>
    </ProtectedRoute>
  );
}
