"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { StarRating } from "@/components/star-rating";
import { SelectField } from "@/components/select-field";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPost, apiPatch, apiDelete, ApiError } from "@/lib/api-client";
import type { Review, Book, FamilyGroup } from "@/types";

interface Club {
  id: string;
  name: string;
  description: string | null;
  group_id: string;
  created_at: string;
}

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [groups, setGroups] = useState<FamilyGroup[]>([]);
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);
  const [borrowedBooks, setBorrowedBooks] = useState<Book[]>([]);
  const [sharedReviews, setSharedReviews] = useState<Review[]>([]);

  const [showForm, setShowForm] = useState(false);
  const [editingReview, setEditingReview] = useState<Review | null>(null);
  const [formBookId, setFormBookId] = useState("");
  const [formRating, setFormRating] = useState(0);
  const [formText, setFormText] = useState("");
  const [formVisibility, setFormVisibility] = useState<"private" | "shared">("private");
  const [formTarget, setFormTarget] = useState("");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Review | null>(null);

  const { showToast } = useToast();

  useEffect(() => {
    async function loadData() {
      try {
        const [reviewsData, booksData, groupsData, clubsData, sharedData] =
          await Promise.all([
            apiGet<Review[]>("/reviews"),
            apiGet<Book[]>("/books"),
            apiGet<FamilyGroup[]>("/groups"),
            apiGet<Club[]>("/clubs"),
            apiGet<Review[]>("/reviews/shared").catch(() => [] as Review[]),
          ]);
        setReviews(reviewsData);
        setBooks(booksData);
        setGroups(groupsData);
        setClubs(clubsData);
        setSharedReviews(sharedData);

        try {
          const borrowedLoans = await apiGet<
            { book_id: string | null; book_title: string }[]
          >("/loans/borrowed?status=active");
          const existingBookIds = new Set(booksData.map((b) => b.id));
          const extraBooks: Book[] = [];
          for (const loan of borrowedLoans) {
            if (loan.book_id && !existingBookIds.has(loan.book_id)) {
              existingBookIds.add(loan.book_id);
              extraBooks.push({
                id: loan.book_id,
                title: loan.book_title,
                author: "",
                genres: [],
                description: null,
                pages: null,
                isbn: null,
                created_at: "",
              });
            }
          }
          if (extraBooks.length > 0) setBorrowedBooks(extraBooks);
        } catch {
          // optional
        }
      } catch {
        // partial failure acceptable
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const resetForm = () => {
    setFormBookId("");
    setFormRating(0);
    setFormText("");
    setFormVisibility("private");
    setFormTarget("");
    setFormError("");
    setEditingReview(null);
    setShowForm(false);
  };

  const openEditForm = (review: Review) => {
    setEditingReview(review);
    setFormBookId(review.book_id);
    setFormRating(review.rating);
    setFormText(review.text ?? "");
    setFormVisibility(review.visibility);
    if (
      review.visibility === "shared" &&
      review.shared_with_type &&
      review.shared_with_id
    ) {
      setFormTarget(`${review.shared_with_type}:${review.shared_with_id}`);
    } else {
      setFormTarget("");
    }
    setFormError("");
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (!formBookId) { setFormError("Debes seleccionar un libro"); return; }
    if (formRating < 1 || formRating > 5) { setFormError("Debes asignar una calificación de 1 a 5 estrellas"); return; }
    if (formVisibility === "shared" && !formTarget) { setFormError("Debes seleccionar con quién compartir la reseña"); return; }

    setSubmitting(true);

    let sharedWithType: "group" | "club" | undefined;
    let sharedWithId: string | undefined;
    if (formVisibility === "shared" && formTarget) {
      const [type, id] = formTarget.split(":");
      sharedWithType = type as "group" | "club";
      sharedWithId = id;
    }

    try {
      if (editingReview) {
        const updated = await apiPatch<Review>(`/reviews/${editingReview.id}`, {
          rating: formRating,
          text: formText.trim() || undefined,
          visibility: formVisibility,
          shared_with_type: formVisibility === "shared" ? sharedWithType : undefined,
          shared_with_id: formVisibility === "shared" ? sharedWithId : undefined,
        });
        setReviews((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
        showToast("Reseña actualizada", "success");
      } else {
        const created = await apiPost<Review>("/reviews", {
          book_id: formBookId,
          rating: formRating,
          text: formText.trim() || undefined,
          visibility: formVisibility,
          shared_with_type: formVisibility === "shared" ? sharedWithType : undefined,
          shared_with_id: formVisibility === "shared" ? sharedWithId : undefined,
        });
        setReviews((prev) => [created, ...prev]);
        showToast("Reseña creada", "success");
      }
      resetForm();
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === "string") {
        setFormError(err.detail);
      } else {
        showToast("Error al guardar la reseña", "error");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiDelete(`/reviews/${deleteTarget.id}`);
      setReviews((prev) => prev.filter((r) => r.id !== deleteTarget.id));
      showToast("Reseña eliminada", "success");
    } catch {
      showToast("Error al eliminar la reseña", "error");
    } finally {
      setDeleteTarget(null);
    }
  };

  const getBookTitle = (bookId: string): string => {
    const book = books.find((b) => b.id === bookId);
    if (book) return book.title;
    const borrowed = borrowedBooks.find((b) => b.id === bookId);
    if (borrowed) return borrowed.title;
    return bookId;
  };

  const getVisibilityBadge = (review: Review) => {
    if (review.visibility === "private") {
      return (
        <span className="badge-pending">Privada</span>
      );
    }
    let targetName = "";
    if (review.shared_with_type === "group") {
      const group = groups.find((g) => g.id === review.shared_with_id);
      targetName = group ? `Grupo: ${group.name}` : "Grupo";
    } else if (review.shared_with_type === "club") {
      const club = clubs.find((c) => c.id === review.shared_with_id);
      targetName = club ? `Club: ${club.name}` : "Club";
    }
    return (
      <span className="badge-read">Compartida — {targetName}</span>
    );
  };

  const targetOptions = [
    ...groups.map((g) => ({ value: `group:${g.id}`, label: `Grupo: ${g.name}` })),
    ...clubs.map((c) => ({ value: `club:${c.id}`, label: `Club: ${c.name}` })),
  ];

  const bookOptions = [
    ...books.map((b) => ({ value: b.id, label: `${b.title} — ${b.author}` })),
    ...borrowedBooks.map((b) => ({ value: b.id, label: `${b.title} (prestado)` })),
  ];

  return (
    <ProtectedRoute>
      <Navigation />
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h1
              className="text-2xl font-bold"
              style={{
                fontFamily: "var(--font-playfair), Georgia, serif",
                color: "var(--color-walnut)",
              }}
            >
              Mis Reseñas
            </h1>
            <button
              type="button"
              onClick={() => { resetForm(); setShowForm(true); }}
              className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-mahogany)")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-walnut)")
              }
            >
              Nueva reseña
            </button>
          </div>

          {/* Create / Edit Form */}
          {showForm && (
            <form
              onSubmit={handleSubmit}
              className="mb-6 rounded-lg p-5 space-y-4"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
                boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
              }}
            >
              <h2
                className="text-lg font-semibold"
                style={{
                  fontFamily: "var(--font-playfair), Georgia, serif",
                  color: "var(--color-walnut)",
                }}
              >
                {editingReview ? "Editar reseña" : "Nueva reseña"}
              </h2>

              {!editingReview && (
                <SelectField
                  label="Libro"
                  name="review-book"
                  options={bookOptions}
                  value={formBookId}
                  onChange={(e) => setFormBookId(e.target.value)}
                  required
                  placeholder="Selecciona un libro"
                />
              )}

              {editingReview && (
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium" style={{ color: "var(--color-ink-soft)" }}>
                    Libro
                  </span>
                  <span className="text-sm" style={{ color: "var(--color-ink)" }}>
                    {getBookTitle(editingReview.book_id)}
                  </span>
                </div>
              )}

              {/* Star Rating */}
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium" style={{ color: "var(--color-ink-soft)" }}>
                  Calificación{" "}
                  <span style={{ color: "var(--color-leather)" }}>*</span>
                </span>
                <StarRating value={formRating} onChange={setFormRating} />
              </div>

              {/* Text */}
              <div className="flex flex-col gap-1">
                <label
                  htmlFor="review-text"
                  className="text-sm font-medium"
                  style={{ color: "var(--color-ink-soft)" }}
                >
                  Comentario (opcional)
                </label>
                <textarea
                  id="review-text"
                  name="review-text"
                  value={formText}
                  onChange={(e) => setFormText(e.target.value)}
                  placeholder="Escribe tu opinión sobre el libro..."
                  rows={3}
                  className="rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
                  style={{
                    borderColor: "var(--color-border)",
                    background: "var(--color-cream)",
                    color: "var(--color-ink)",
                  }}
                />
              </div>

              {/* Visibility */}
              <fieldset className="flex flex-col gap-2">
                <legend className="text-sm font-medium mb-1" style={{ color: "var(--color-ink-soft)" }}>
                  Visibilidad{" "}
                  <span style={{ color: "var(--color-leather)" }}>*</span>
                </legend>
                <div className="flex gap-4">
                  {(["private", "shared"] as const).map((vis) => (
                    <label key={vis} className="flex items-center gap-2 cursor-pointer text-sm" style={{ color: "var(--color-ink-soft)" }}>
                      <input
                        type="radio"
                        name="review-visibility"
                        value={vis}
                        checked={formVisibility === vis}
                        onChange={() => {
                          setFormVisibility(vis);
                          if (vis === "private") setFormTarget("");
                        }}
                        style={{ accentColor: "var(--color-teak)" }}
                      />
                      {vis === "private" ? "Privada" : "Compartida"}
                    </label>
                  ))}
                </div>
              </fieldset>

              {formVisibility === "shared" && (
                <SelectField
                  label="Compartir con"
                  name="review-target"
                  options={targetOptions}
                  value={formTarget}
                  onChange={(e) => setFormTarget(e.target.value)}
                  required
                  placeholder="Selecciona un grupo o club"
                />
              )}

              {formError && (
                <p className="text-sm" style={{ color: "var(--color-leather)" }} role="alert">
                  {formError}
                </p>
              )}

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={resetForm}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                  style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)", background: "transparent" }}
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
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
                  onMouseEnter={(e) => {
                    if (!submitting)
                      (e.currentTarget as HTMLButtonElement).style.background =
                        "var(--color-mahogany)";
                  }}
                  onMouseLeave={(e) => {
                    if (!submitting)
                      (e.currentTarget as HTMLButtonElement).style.background =
                        "var(--color-walnut)";
                  }}
                >
                  {submitting ? "Guardando..." : editingReview ? "Guardar cambios" : "Crear reseña"}
                </button>
              </div>
            </form>
          )}

          {loading && <Skeleton variant="card" count={3} />}

          {!loading && reviews.length === 0 && !showForm && (
            <div
              className="rounded-lg p-8 text-center"
              style={{ background: "var(--color-cream)", border: "1px solid var(--color-border)" }}
            >
              <p className="text-base font-medium mb-2" style={{ color: "var(--color-walnut)" }}>
                No has escrito reseñas aún.
              </p>
              <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                Crea una reseña para compartir tu opinión sobre un libro.
              </p>
            </div>
          )}

          {/* My Reviews */}
          {!loading && reviews.length > 0 && (
            <div className="space-y-3">
              {reviews.map((review) => (
                <div
                  key={review.id}
                  className="rounded-lg px-5 py-4"
                  style={{
                    background: "var(--color-cream)",
                    border: "1px solid var(--color-border)",
                    boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                  }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h2
                        className="text-base font-semibold truncate"
                        style={{
                          fontFamily: "var(--font-playfair), Georgia, serif",
                          color: "var(--color-walnut)",
                        }}
                      >
                        {getBookTitle(review.book_id)}
                      </h2>
                      <div className="mt-1 flex items-center gap-3">
                        <StarRating value={review.rating} readonly />
                        {getVisibilityBadge(review)}
                      </div>
                      {review.text && (
                        <p
                          className="mt-2 text-sm line-clamp-2"
                          style={{ color: "var(--color-ink-soft)" }}
                        >
                          {review.text}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => openEditForm(review)}
                        className="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
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
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteTarget(review)}
                        className="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
                        style={{
                          border: "1px solid var(--color-leather)",
                          color: "var(--color-leather)",
                          background: "transparent",
                        }}
                        onMouseEnter={(e) => {
                          (e.currentTarget as HTMLButtonElement).style.background =
                            "#FAF0E8";
                        }}
                        onMouseLeave={(e) => {
                          (e.currentTarget as HTMLButtonElement).style.background =
                            "transparent";
                        }}
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Shared Reviews from Others */}
          {!loading && sharedReviews.length > 0 && (
            <section className="mt-8">
              <h2
                className="text-xl font-bold mb-4"
                style={{
                  fontFamily: "var(--font-playfair), Georgia, serif",
                  color: "var(--color-walnut)",
                }}
              >
                Reseñas compartidas conmigo
              </h2>
              <div className="space-y-3">
                {sharedReviews.map((review) => (
                  <div
                    key={review.id}
                    className="rounded-lg px-5 py-4"
                    style={{
                      background: "#FDF6E3",
                      border: "1px solid var(--color-brass)",
                      boxShadow: "0 1px 3px rgba(28,16,8,0.06)",
                    }}
                  >
                    <div className="flex-1 min-w-0">
                      <h3
                        className="text-base font-semibold truncate"
                        style={{
                          fontFamily: "var(--font-playfair), Georgia, serif",
                          color: "var(--color-walnut)",
                        }}
                      >
                        {getBookTitle(review.book_id)}
                      </h3>
                      <div className="mt-1 flex items-center gap-3">
                        <StarRating value={review.rating} readonly />
                        {getVisibilityBadge(review)}
                      </div>
                      {review.text && (
                        <p
                          className="mt-2 text-sm line-clamp-3"
                          style={{ color: "var(--color-ink-soft)" }}
                        >
                          {review.text}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar reseña"
        message="¿Estás seguro de que quieres eliminar esta reseña? Esta acción no se puede deshacer."
        confirmText="Eliminar"
        cancelText="Cancelar"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        destructive
      />
    </ProtectedRoute>
  );
}
