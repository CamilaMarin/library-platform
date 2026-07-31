"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";
import { apiPut, apiPatch, apiPost, apiGet, apiPostForm } from "@/lib/api-client";
import { LoanForm } from "@/components/loan-form";
import type { Book, CopyWithLoanStatus, ReadingStatusValue, GroupMember, FamilyGroup } from "@/types";

interface BookDetailModalProps {
  book: Book | null;
  copies: CopyWithLoanStatus[];
  open: boolean;
  loadingCopies: boolean;
  onClose: () => void;
  readingStatus?: { status: string; current_page: number | null } | null;
  onProgressUpdate?: () => void;
  onStatusChange?: (bookId: string, status: ReadingStatusValue | null) => void;
  /** If provided, shows an edit button. Called with updated book after save. */
  onBookUpdate?: (updatedBook: Book) => void;
  /** If provided, enables "Agregar copia" action */
  onCopyAdded?: () => void;
  /** If provided, enables "Prestar" action on available physical copies */
  onLoanCreated?: () => void;
}

export function BookDetailModal({
  book,
  copies,
  open,
  loadingCopies,
  onClose,
  readingStatus,
  onProgressUpdate,
  onStatusChange,
  onBookUpdate,
  onCopyAdded,
  onLoanCreated,
}: BookDetailModalProps) {
  const router = useRouter();
  const dialogRef = useRef<HTMLDivElement>(null);
  const digitalFileRef = useRef<HTMLInputElement>(null);
  const [pageInput, setPageInput] = useState<string>("");
  const [savingProgress, setSavingProgress] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    title: "",
    author: "",
    pages: "",
    genres: "",
    description: "",
    isbn: "",
  });
  const [saving, setSaving] = useState(false);

  // Add copy state
  const [showAddCopy, setShowAddCopy] = useState(false);
  const [addingCopy, setAddingCopy] = useState(false);

  // Digital upload state
  const [uploadingDigital, setUploadingDigital] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Loan state
  const [lendCopyId, setLendCopyId] = useState<string | null>(null);
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);

  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Trap focus inside modal and prevent body scroll
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  // Reset page input when modal opens/closes or book changes
  useEffect(() => {
    setPageInput("");
  }, [open, book?.id]);

  // Populate edit form when entering edit mode
  useEffect(() => {
    if (editing && book) {
      setEditForm({
        title: book.title,
        author: book.author,
        pages: book.pages?.toString() || "",
        genres: book.genres.join(", "),
        description: book.description || "",
        isbn: book.isbn || "",
      });
    }
  }, [editing, book]);

  // Reset editing and copy/loan state when modal closes
  useEffect(() => {
    if (!open) {
      setEditing(false);
      setShowAddCopy(false);
      setLendCopyId(null);
      setGroupMembers([]);
    }
  }, [open]);

  const handleSaveEdit = async () => {
    if (!book) return;
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {};
      if (editForm.title.trim() && editForm.title !== book.title) payload.title = editForm.title.trim();
      if (editForm.author.trim() && editForm.author !== book.author) payload.author = editForm.author.trim();
      if (editForm.pages && parseInt(editForm.pages) !== book.pages) payload.pages = parseInt(editForm.pages);
      if (editForm.genres !== book.genres.join(", ")) {
        payload.genres = editForm.genres.split(",").map((g) => g.trim()).filter(Boolean);
      }
      if (editForm.description !== (book.description || "")) payload.description = editForm.description;
      if (editForm.isbn !== (book.isbn || "")) payload.isbn = editForm.isbn || null;

      if (Object.keys(payload).length > 0) {
        const updated = await apiPatch<Book>(`/books/${book.id}`, payload);
        if (onBookUpdate) onBookUpdate(updated);
      }
      setEditing(false);
    } catch {
      // silent — could add error toast
    } finally {
      setSaving(false);
    }
  };

  const handleAddCopy = async () => {
    if (!book) return;
    setAddingCopy(true);
    try {
      await apiPost(`/copies/physical`, { book_id: book.id });
      if (onCopyAdded) onCopyAdded();
      setShowAddCopy(false);
    } catch {
      // silent
    } finally {
      setAddingCopy(false);
    }
  };

  const handleDigitalUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!book || !e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];

    // Client-side max file size: 50MB
    const MAX_SIZE = 50 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setUploadError("El archivo excede el tamaño máximo de 50MB.");
      // Reset file input
      if (digitalFileRef.current) digitalFileRef.current.value = "";
      return;
    }

    setUploadingDigital(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append("book_id", book.id);
      formData.append("file", file);
      await apiPostForm("/copies/digital", formData);
      if (onCopyAdded) onCopyAdded();
    } catch {
      setUploadError("Error al subir el archivo.");
    } finally {
      setUploadingDigital(false);
      if (digitalFileRef.current) digitalFileRef.current.value = "";
    }
  };

  const handleLendClick = async (copyId: string) => {
    setLendCopyId(copyId);
    setLoadingMembers(true);
    try {
      const groups = await apiGet<FamilyGroup[]>("/groups");
      if (groups.length > 0) {
        const memberPromises = groups.map((g) => apiGet<GroupMember[]>(`/groups/${g.id}/members`));
        const allArrays = await Promise.all(memberPromises);
        const seen = new Set<string>();
        const allMembers: GroupMember[] = [];
        for (const members of allArrays) {
          for (const m of members) {
            if (!seen.has(m.user_id)) {
              seen.add(m.user_id);
              allMembers.push(m);
            }
          }
        }
        setGroupMembers(allMembers);
      }
    } catch {
      setGroupMembers([]);
    } finally {
      setLoadingMembers(false);
    }
  };

  if (!open || !book) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="book-detail-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        style={{ background: "rgba(28, 16, 8, 0.5)" }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Card */}
      <div
        ref={dialogRef}
        className="relative w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-xl p-6"
        style={{
          background: "var(--color-parchment)",
          border: "1px solid var(--color-border)",
          boxShadow: "0 20px 60px -12px rgba(28, 16, 8, 0.35)",
        }}
      >
        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar detalle del libro"
          className="absolute top-4 right-4 rounded-full p-1.5 transition-colors"
          style={{
            color: "var(--color-ink-faint)",
            background: "transparent",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "var(--color-cream)";
            (e.currentTarget as HTMLButtonElement).style.color = "var(--color-walnut)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "transparent";
            (e.currentTarget as HTMLButtonElement).style.color = "var(--color-ink-faint)";
          }}
        >
          <X size={18} />
        </button>

        {/* Edit button — only when owner can edit */}
        {onBookUpdate && !editing && (
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="absolute top-4 right-12 rounded-full px-3 py-1 text-xs font-medium transition-colors"
            style={{
              color: "var(--color-brass)",
              border: "1px solid var(--color-brass)",
              background: "transparent",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "var(--color-brass)";
              (e.currentTarget as HTMLButtonElement).style.color = "var(--color-cream)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "transparent";
              (e.currentTarget as HTMLButtonElement).style.color = "var(--color-brass)";
            }}
          >
            Editar
          </button>
        )}

        {/* Book info — view or edit mode */}
        {!editing ? (
          <>
            <h2
              id="book-detail-title"
              className="text-xl font-bold pr-20 mb-1"
              style={{
                fontFamily: "var(--font-playfair), Georgia, serif",
                color: "var(--color-walnut)",
              }}
            >
              {book.title}
            </h2>
            <p className="text-sm mb-4" style={{ color: "var(--color-ink-faint)" }}>
              {book.author}
            </p>

            {book.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {book.genres.map((genre) => (
                  <span
                    key={genre}
                    className="rounded-full px-2.5 py-0.5 text-xs font-medium"
                    style={{
                      background: "var(--color-cream)",
                      color: "var(--color-teak)",
                      border: "1px solid var(--color-border)",
                    }}
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}

            <div className="flex flex-wrap gap-4 text-xs mb-4" style={{ color: "var(--color-ink-soft)" }}>
              {book.pages && <span>{book.pages} páginas</span>}
              {book.isbn && <span>ISBN: {book.isbn}</span>}
            </div>

            {book.description && (
              <p className="text-sm leading-relaxed mb-5" style={{ color: "var(--color-ink-soft)" }}>
                {book.description}
              </p>
            )}
          </>
        ) : (
          /* Edit form */
          <div className="space-y-3 mb-5 pr-8">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium" style={{ color: "var(--color-ink-faint)" }}>Título</label>
              <input
                type="text"
                value={editForm.title}
                onChange={(e) => setEditForm((f) => ({ ...f, title: e.target.value }))}
                className="rounded-md px-3 py-1.5 text-sm"
                style={{ border: "1px solid var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium" style={{ color: "var(--color-ink-faint)" }}>Autor</label>
              <input
                type="text"
                value={editForm.author}
                onChange={(e) => setEditForm((f) => ({ ...f, author: e.target.value }))}
                className="rounded-md px-3 py-1.5 text-sm"
                style={{ border: "1px solid var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }}
              />
            </div>
            <div className="flex gap-3">
              <div className="flex flex-col gap-1 w-24">
                <label className="text-xs font-medium" style={{ color: "var(--color-ink-faint)" }}>Páginas</label>
                <input
                  type="number"
                  min="1"
                  value={editForm.pages}
                  onChange={(e) => setEditForm((f) => ({ ...f, pages: e.target.value }))}
                  className="rounded-md px-3 py-1.5 text-sm"
                  style={{ border: "1px solid var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }}
                />
              </div>
              <div className="flex flex-col gap-1 flex-1">
                <label className="text-xs font-medium" style={{ color: "var(--color-ink-faint)" }}>ISBN</label>
                <input
                  type="text"
                  value={editForm.isbn}
                  onChange={(e) => setEditForm((f) => ({ ...f, isbn: e.target.value }))}
                  className="rounded-md px-3 py-1.5 text-sm"
                  style={{ border: "1px solid var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }}
                />
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium" style={{ color: "var(--color-ink-faint)" }}>Géneros (separados por coma)</label>
              <input
                type="text"
                value={editForm.genres}
                onChange={(e) => setEditForm((f) => ({ ...f, genres: e.target.value }))}
                placeholder="Ficción, Fantasía, ..."
                className="rounded-md px-3 py-1.5 text-sm"
                style={{ border: "1px solid var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium" style={{ color: "var(--color-ink-faint)" }}>Descripción</label>
              <textarea
                value={editForm.description}
                onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                rows={3}
                className="rounded-md px-3 py-1.5 text-sm"
                style={{ border: "1px solid var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }}
              />
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={saving}
                className="rounded-full px-4 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
              >
                {saving ? "Guardando..." : "Guardar"}
              </button>
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="rounded-full px-4 py-1.5 text-xs font-medium transition-colors"
                style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)" }}
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        {/* Divider */}
        <div
          className="mb-4"
          style={{ borderTop: "1px solid var(--color-border)" }}
          aria-hidden="true"
        />

        {/* Copies section */}
        <h3
          className="text-sm font-semibold mb-3"
          style={{ color: "var(--color-walnut)" }}
        >
          Copias
        </h3>

        {loadingCopies && (
          <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
            Cargando copias...
          </p>
        )}

        {!loadingCopies && copies.length === 0 && (
          <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
            No tienes copias de este libro.
          </p>
        )}

        {!loadingCopies && copies.length > 0 && (
          <div className="space-y-2">
            {copies.map((copy) => (
              <div
                key={copy.id}
                className="flex items-center justify-between rounded-md px-3 py-2"
                style={{ background: "var(--color-cream)", border: "1px solid var(--color-border)" }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className="text-xs font-medium uppercase"
                    style={{ color: "var(--color-ink-soft)" }}
                  >
                    {copy.format === "physical" ? "Física" : "Digital"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-[11px] font-medium"
                    style={{
                      background:
                        copy.loan_status === "available"
                          ? "var(--color-reading)"
                          : "var(--color-brass)",
                      color: "var(--color-cream)",
                    }}
                  >
                    {copy.loan_status === "available" ? "Disponible" : "Prestada"}
                  </span>
                  {copy.format === "digital" && (
                    <button
                      type="button"
                      onClick={() => router.push(`/reader/${copy.id}`)}
                      className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors"
                      style={{ background: "var(--color-reading)", color: "var(--color-cream)" }}
                    >
                      Leer
                    </button>
                  )}
                  {onLoanCreated && copy.format === "physical" && copy.loan_status === "available" && lendCopyId !== copy.id && (
                    <button
                      type="button"
                      onClick={() => handleLendClick(copy.id)}
                      className="rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors"
                      style={{ background: "var(--color-teak)", color: "var(--color-cream)" }}
                    >
                      Prestar
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Copy/Loan actions — only when owner (onCopyAdded provided) */}
        {onCopyAdded && (
          <div className="mt-3 flex flex-wrap gap-2">
            {!showAddCopy && (
              <button
                type="button"
                onClick={() => setShowAddCopy(true)}
                className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors"
                style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)" }}
              >
                + Agregar copia física
              </button>
            )}
            {showAddCopy && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleAddCopy}
                  disabled={addingCopy}
                  className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                  style={{ background: "var(--color-reading)", color: "var(--color-cream)" }}
                >
                  {addingCopy ? "..." : "Confirmar copia física"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddCopy(false)}
                  className="rounded-full px-3 py-1.5 text-xs font-medium"
                  style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)" }}
                >
                  Cancelar
                </button>
              </div>
            )}
            <button
              type="button"
              onClick={() => digitalFileRef.current?.click()}
              disabled={uploadingDigital}
              className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
              style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)" }}
            >
              {uploadingDigital ? "Subiendo..." : "+ Subir archivo digital"}
            </button>
            <input
              ref={digitalFileRef}
              type="file"
              accept=".epub,.pdf"
              onChange={handleDigitalUpload}
              className="hidden"
              aria-hidden="true"
            />
            {uploadError && (
              <p className="w-full text-xs mt-1" style={{ color: "var(--color-mahogany, #b91c1c)" }}>
                {uploadError}
              </p>
            )}
          </div>
        )}

        {/* Inline loan form for a specific copy */}
        {lendCopyId && (
          <div className="mt-3 p-3 rounded-md" style={{ background: "#EDF7F0", border: "1px solid var(--color-reading)" }}>
            {loadingMembers ? (
              <p className="text-xs" style={{ color: "var(--color-ink-faint)" }}>Cargando miembros...</p>
            ) : groupMembers.length === 0 ? (
              <div>
                <p className="text-xs mb-2" style={{ color: "var(--color-ink-soft)" }}>No hay miembros para prestar.</p>
                <button type="button" onClick={() => setLendCopyId(null)}
                  className="rounded-full px-3 py-1 text-xs" style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)" }}>
                  Cancelar
                </button>
              </div>
            ) : (
              <LoanForm
                copyId={lendCopyId}
                groupMembers={groupMembers}
                onSuccess={() => { setLendCopyId(null); setGroupMembers([]); if (onLoanCreated) onLoanCreated(); }}
                onCancel={() => { setLendCopyId(null); setGroupMembers([]); }}
              />
            )}
          </div>
        )}

        {/* Reading Status selector */}
        {onStatusChange && (
          <>
            <div className="my-4" style={{ borderTop: "1px solid var(--color-border)" }} aria-hidden="true" />
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--color-walnut)" }}>
              Estado de lectura
            </h3>
            <div className="flex flex-wrap gap-2">
              {[
                { value: "reading", label: "Leyendo", bg: "var(--color-reading)" },
                { value: "want_to_read", label: "Quiero leer", bg: "var(--color-teak)" },
                { value: "read", label: "Leído", bg: "var(--color-walnut)" },
                { value: "dnf", label: "No terminado", bg: "var(--color-mahogany)" },
              ].map((opt) => {
                const isActive = readingStatus?.status === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => onStatusChange(book!.id, isActive ? null : opt.value as ReadingStatusValue)}
                    className="rounded-full px-3 py-1.5 text-xs font-medium transition-all"
                    style={{
                      background: isActive ? opt.bg : "var(--color-cream)",
                      color: isActive ? "var(--color-cream)" : "var(--color-ink-soft)",
                      border: `1px solid ${isActive ? opt.bg : "var(--color-border)"}`,
                      opacity: isActive ? 1 : 0.8,
                    }}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </>
        )}

        {/* Reading Progress — only when status is "reading" */}
        {readingStatus?.status === "reading" && book && (
          <>
            <div className="my-4" style={{ borderTop: "1px solid var(--color-border)" }} aria-hidden="true" />
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--color-walnut)" }}>
              Progreso de lectura
            </h3>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <label htmlFor="page-input" className="text-sm" style={{ color: "var(--color-ink-soft)" }}>
                  Página
                </label>
                <input
                  id="page-input"
                  type="number"
                  min="0"
                  max={book.pages || undefined}
                  value={pageInput || readingStatus.current_page || ""}
                  onChange={(e) => setPageInput(e.target.value)}
                  placeholder={readingStatus.current_page?.toString() || "0"}
                  className="w-20 rounded-md px-2 py-1 text-sm text-center"
                  style={{
                    border: "1px solid var(--color-border)",
                    background: "var(--color-cream)",
                    color: "var(--color-ink)",
                  }}
                />
                {book.pages && (
                  <span className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                    / {book.pages}
                  </span>
                )}
              </div>
              <button
                type="button"
                disabled={savingProgress || !pageInput}
                onClick={async () => {
                  if (!pageInput || !book) return;
                  setSavingProgress(true);
                  try {
                    await apiPut(`/books/${book.id}/status`, {
                      status: "reading",
                      current_page: parseInt(pageInput, 10),
                    });
                    if (onProgressUpdate) onProgressUpdate();
                    setPageInput("");
                  } catch {
                    // silent fail
                  } finally {
                    setSavingProgress(false);
                  }
                }}
                className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  background: "var(--color-walnut)",
                  color: "var(--color-cream)",
                  borderRadius: "6px",
                }}
              >
                {savingProgress ? "..." : "Guardar"}
              </button>
            </div>
            {readingStatus.current_page && book.pages && (
              <div className="mt-2">
                <div
                  className="h-2 rounded-full overflow-hidden"
                  style={{ background: "var(--color-parchment-deep, #E0D0AE)" }}
                >
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, Math.round((readingStatus.current_page / book.pages) * 100))}%`,
                      background: "var(--color-reading)",
                    }}
                  />
                </div>
                <p className="text-xs mt-1" style={{ color: "var(--color-ink-faint)" }}>
                  {Math.round((readingStatus.current_page / book.pages) * 100)}% completado
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
