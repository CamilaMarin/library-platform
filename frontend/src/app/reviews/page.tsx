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

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingReview, setEditingReview] = useState<Review | null>(null);
  const [formBookId, setFormBookId] = useState("");
  const [formRating, setFormRating] = useState(0);
  const [formText, setFormText] = useState("");
  const [formVisibility, setFormVisibility] = useState<"private" | "shared">("private");
  const [formTarget, setFormTarget] = useState("");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Delete state
  const [deleteTarget, setDeleteTarget] = useState<Review | null>(null);

  const { showToast } = useToast();

  useEffect(() => {
    async function loadData() {
      try {
        const [reviewsData, booksData, groupsData, clubsData] = await Promise.all([
          apiGet<Review[]>("/reviews"),
          apiGet<Book[]>("/books"),
          apiGet<FamilyGroup[]>("/groups"),
          apiGet<Club[]>("/clubs"),
        ]);
        setReviews(reviewsData);
        setBooks(booksData);
        setGroups(groupsData);
        setClubs(clubsData);
      } catch {
        // Partial failure is acceptable
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

  const openCreateForm = () => {
    resetForm();
    setShowForm(true);
  };

  const openEditForm = (review: Review) => {
    setEditingReview(review);
    setFormBookId(review.book_id);
    setFormRating(review.rating);
    setFormText(review.text ?? "");
    setFormVisibility(review.visibility);
    if (review.visibility === "shared" && review.shared_with_type && review.shared_with_id) {
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

    // Validation
    if (!formBookId) {
      setFormError("Debes seleccionar un libro");
      return;
    }
    if (formRating < 1 || formRating > 5) {
      setFormError("Debes asignar una calificación de 1 a 5 estrellas");
      return;
    }
    if (formVisibility === "shared" && !formTarget) {
      setFormError("Debes seleccionar con quién compartir la reseña");
      return;
    }

    setSubmitting(true);

    // Parse target
    let sharedWithType: "group" | "club" | undefined;
    let sharedWithId: string | undefined;
    if (formVisibility === "shared" && formTarget) {
      const [type, id] = formTarget.split(":");
      sharedWithType = type as "group" | "club";
      sharedWithId = id;
    }

    try {
      if (editingReview) {
        // Edit
        const updated = await apiPatch<Review>(`/reviews/${editingReview.id}`, {
          rating: formRating,
          text: formText.trim() || undefined,
          visibility: formVisibility,
          shared_with_type: formVisibility === "shared" ? sharedWithType : undefined,
          shared_with_id: formVisibility === "shared" ? sharedWithId : undefined,
        });
        setReviews((prev) =>
          prev.map((r) => (r.id === updated.id ? updated : r))
        );
        showToast("Reseña actualizada", "success");
      } else {
        // Create
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
    return book ? book.title : bookId;
  };

  const getVisibilityBadge = (review: Review) => {
    if (review.visibility === "private") {
      return (
        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
          Privada
        </span>
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
      <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
        Compartida — {targetName}
      </span>
    );
  };

  // Build target options for the share selector
  const targetOptions = [
    ...groups.map((g) => ({ value: `group:${g.id}`, label: `Grupo: ${g.name}` })),
    ...clubs.map((c) => ({ value: `club:${c.id}`, label: `Club: ${c.name}` })),
  ];

  // Build book options for the selector
  const bookOptions = books.map((b) => ({
    value: b.id,
    label: `${b.title} — ${b.author}`,
  }));

  return (
    <ProtectedRoute>
      <Navigation />
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Mis Reseñas</h1>
            <button
              type="button"
              onClick={openCreateForm}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Nueva reseña
            </button>
          </div>

          {/* Create/Edit Form */}
          {showForm && (
            <form
              onSubmit={handleSubmit}
              className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm space-y-4"
            >
              <h2 className="text-lg font-semibold text-gray-900">
                {editingReview ? "Editar reseña" : "Nueva reseña"}
              </h2>

              {/* Book selector (disabled when editing) */}
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
                  <span className="text-sm font-medium text-gray-700">Libro</span>
                  <span className="text-sm text-gray-600">
                    {getBookTitle(editingReview.book_id)}
                  </span>
                </div>
              )}

              {/* Star Rating */}
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-gray-700">
                  Calificación <span className="text-red-500">*</span>
                </span>
                <StarRating value={formRating} onChange={setFormRating} />
              </div>

              {/* Text */}
              <div className="flex flex-col gap-1">
                <label
                  htmlFor="review-text"
                  className="text-sm font-medium text-gray-700"
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
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Visibility */}
              <fieldset className="flex flex-col gap-2">
                <legend className="text-sm font-medium text-gray-700 mb-1">
                  Visibilidad <span className="text-red-500">*</span>
                </legend>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="review-visibility"
                      value="private"
                      checked={formVisibility === "private"}
                      onChange={() => {
                        setFormVisibility("private");
                        setFormTarget("");
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Privada</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="review-visibility"
                      value="shared"
                      checked={formVisibility === "shared"}
                      onChange={() => setFormVisibility("shared")}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Compartida</span>
                  </label>
                </div>
              </fieldset>

              {/* Target selector (shown only when shared) */}
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

              {/* Form error */}
              {formError && (
                <p className="text-sm text-red-600" role="alert">
                  {formError}
                </p>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={resetForm}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {submitting
                    ? "Guardando..."
                    : editingReview
                    ? "Guardar cambios"
                    : "Crear reseña"}
                </button>
              </div>
            </form>
          )}

          {/* Loading State */}
          {loading && <Skeleton variant="card" count={3} />}

          {/* Empty State */}
          {!loading && reviews.length === 0 && !showForm && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
              <p className="text-lg font-medium text-gray-900 mb-2">
                No has escrito reseñas aún.
              </p>
              <p className="text-sm text-gray-500">
                Crea una reseña para compartir tu opinión sobre un libro.
              </p>
            </div>
          )}

          {/* Reviews List */}
          {!loading && reviews.length > 0 && (
            <div className="space-y-3">
              {reviews.map((review) => (
                <div
                  key={review.id}
                  className="rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h2 className="text-base font-semibold text-gray-900 truncate">
                        {getBookTitle(review.book_id)}
                      </h2>
                      <div className="mt-1 flex items-center gap-3">
                        <StarRating value={review.rating} readonly />
                        {getVisibilityBadge(review)}
                      </div>
                      {review.text && (
                        <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                          {review.text}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => openEditForm(review)}
                        className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteTarget(review)}
                        className="rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 transition-colors"
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Delete Confirmation */}
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
