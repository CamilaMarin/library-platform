"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { useToast } from "@/context/toast-context";
import { useAuth } from "@/context/auth-context";
import { apiGet, apiPost, ApiError } from "@/lib/api-client";

// === Local Interfaces ===

interface ClubDetail {
  id: string;
  name: string;
  description: string | null;
  group_id: string;
  active_book_id: string | null;
  created_at: string;
}

interface ClubMember {
  id: string;
  user_id: string;
  club_id: string;
  name: string;
  role: string;
  created_at: string;
}

interface Comment {
  id: string;
  user_id: string;
  text: string;
  is_spoiler: boolean;
  created_at: string;
}

interface BookOption {
  id: string;
  title: string;
  author: string;
}

// === Component ===

export default function ClubDetailPage() {
  const params = useParams();
  const clubId = params.id as string;
  const { user } = useAuth();
  const { showToast } = useToast();

  // Club data state
  const [club, setClub] = useState<ClubDetail | null>(null);
  const [members, setMembers] = useState<ClubMember[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  // Comment form state
  const [commentText, setCommentText] = useState("");
  const [isSpoiler, setIsSpoiler] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);

  // Active book state
  const [showSetBookForm, setShowSetBookForm] = useState(false);
  const [availableBooks, setAvailableBooks] = useState<BookOption[]>([]);
  const [selectedBookId, setSelectedBookId] = useState("");
  const [settingBook, setSettingBook] = useState(false);

  // Spoiler reveal state
  const [revealedSpoilers, setRevealedSpoilers] = useState<Set<string>>(
    new Set()
  );

  // Active book title
  const [activeBookTitle, setActiveBookTitle] = useState<string | null>(null);

  const fetchClubData = useCallback(async () => {
    try {
      const [clubData, membersData, commentsData] = await Promise.all([
        apiGet<ClubDetail>(`/clubs/${clubId}`),
        apiGet<ClubMember[]>(`/clubs/${clubId}/members`),
        apiGet<Comment[]>(`/clubs/${clubId}/comments`),
      ]);
      setClub(clubData);
      setMembers(membersData);
      setComments(commentsData);

      if (clubData.active_book_id) {
        try {
          const book = await apiGet<{ id: string; title: string; author: string }>(`/books/${clubData.active_book_id}`);
          setActiveBookTitle(`${book.title} — ${book.author}`);
        } catch {
          setActiveBookTitle(null);
        }
      }
    } catch {
      showToast("Error al cargar los datos del club", "error");
    } finally {
      setLoading(false);
    }
  }, [clubId, showToast]);

  useEffect(() => {
    fetchClubData();
  }, [fetchClubData]);

  const isOwner =
    members.length > 0 &&
    members.some((m) => m.user_id === user?.id && m.role === "owner");

  const handlePostComment = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!commentText.trim()) return;

    setSubmittingComment(true);
    try {
      const newComment = await apiPost<Comment>(`/clubs/${clubId}/comments`, {
        text: commentText.trim(),
        is_spoiler: isSpoiler,
      });
      setComments((prev) => [...prev, newComment]);
      setCommentText("");
      setIsSpoiler(false);
      showToast("Comentario publicado", "success");
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === "string") {
        showToast(err.detail, "error");
      } else {
        showToast("Error al publicar el comentario", "error");
      }
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleSetActiveBook = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedBookId) return;

    setSettingBook(true);
    try {
      await apiPost(`/clubs/${clubId}/active-book`, {
        book_id: selectedBookId,
      });
      setClub((prev) =>
        prev ? { ...prev, active_book_id: selectedBookId } : prev
      );
      // Update the displayed book title from available books
      const selectedBook = availableBooks.find((b) => b.id === selectedBookId);
      if (selectedBook) {
        setActiveBookTitle(`${selectedBook.title} — ${selectedBook.author}`);
      }
      setShowSetBookForm(false);
      setSelectedBookId("");
      showToast("Libro activo actualizado", "success");
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === "string") {
        showToast(err.detail, "error");
      } else {
        showToast("Error al establecer el libro activo", "error");
      }
    } finally {
      setSettingBook(false);
    }
  };

  const handleOpenSetBookForm = async () => {
    setShowSetBookForm(true);
    try {
      const books = await apiGet<BookOption[]>(
        `/clubs/${clubId}/available-books`
      );
      setAvailableBooks(books);
    } catch {
      setAvailableBooks([]);
    }
  };

  const toggleSpoilerReveal = (commentId: string) => {
    setRevealedSpoilers((prev) => {
      const next = new Set(prev);
      if (next.has(commentId)) {
        next.delete(commentId);
      } else {
        next.add(commentId);
      }
      return next;
    });
  };

  const getMemberName = (userId: string): string => {
    const member = members.find((m) => m.user_id === userId);
    return member ? member.name : userId;
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString("es-CL", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <ProtectedRoute>
      <Navigation />
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Loading State */}
          {loading && <Skeleton variant="card" count={3} />}

          {/* Club Content */}
          {!loading && club && (
            <>
              {/* Header */}
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">
                  {club.name}
                </h1>
                {club.description && (
                  <p className="text-sm text-gray-500 mt-1">
                    {club.description}
                  </p>
                )}
              </div>

              {/* Active Book Section */}
              <section className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  📖 Libro activo
                </h2>

                {club.active_book_id ? (
                  <p className="text-sm text-gray-700">
                    {activeBookTitle || club.active_book_id}
                  </p>
                ) : (
                  <p className="text-sm text-gray-500">
                    No hay un libro activo actualmente.
                  </p>
                )}

                {isOwner && !showSetBookForm && (
                  <button
                    type="button"
                    onClick={handleOpenSetBookForm}
                    className="mt-3 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
                  >
                    Establecer libro activo
                  </button>
                )}

                {isOwner && showSetBookForm && (
                  <form
                    onSubmit={handleSetActiveBook}
                    className="mt-4 space-y-3"
                  >
                    <div className="flex flex-col gap-1">
                      <label
                        htmlFor="select-active-book"
                        className="text-sm font-medium text-gray-700"
                      >
                        Seleccionar libro
                      </label>
                      <select
                        id="select-active-book"
                        value={selectedBookId}
                        onChange={(e) => setSelectedBookId(e.target.value)}
                        className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">— Selecciona un libro —</option>
                        {availableBooks.map((book) => (
                          <option key={book.id} value={book.id}>
                            {book.title} — {book.author}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex gap-3">
                      <button
                        type="submit"
                        disabled={!selectedBookId || settingBook}
                        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {settingBook ? "Guardando..." : "Confirmar"}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowSetBookForm(false);
                          setSelectedBookId("");
                        }}
                        className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        Cancelar
                      </button>
                    </div>
                  </form>
                )}
              </section>

              {/* Members Section */}
              <section className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  👥 Miembros ({members.length})
                </h2>

                {members.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    No hay miembros en este club.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {members.map((member) => (
                      <li
                        key={member.id}
                        className="flex items-center justify-between rounded-md border border-gray-100 bg-gray-50 px-3 py-2"
                      >
                        <span className="text-sm text-gray-700">
                          {member.name}
                        </span>
                        {member.role === "owner" && (
                          <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                            Propietario
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              {/* Comments Section */}
              <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  💬 Comentarios
                </h2>

                {comments.length === 0 ? (
                  <p className="text-sm text-gray-500 mb-4">
                    No hay comentarios aún. ¡Sé el primero en comentar!
                  </p>
                ) : (
                  <div className="space-y-3 mb-4">
                    {comments.map((comment) => {
                      const isSpoilerComment = comment.is_spoiler;
                      const isRevealed = revealedSpoilers.has(comment.id);

                      return (
                        <div
                          key={comment.id}
                          className="rounded-md border border-gray-100 bg-gray-50 p-3"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-600">
                              {getMemberName(comment.user_id)}
                            </span>
                            <span className="text-xs text-gray-400">
                              {formatDate(comment.created_at)}
                            </span>
                          </div>

                          {isSpoilerComment && (
                            <span className="inline-block text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded mb-1">
                              ⚠️ Contiene spoilers
                            </span>
                          )}

                          {isSpoilerComment && !isRevealed ? (
                            <button
                              type="button"
                              onClick={() => toggleSpoilerReveal(comment.id)}
                              className="block w-full text-left text-sm text-gray-400 italic hover:text-gray-600 transition-colors"
                            >
                              Haz clic para revelar el contenido con spoilers
                            </button>
                          ) : (
                            <p className="text-sm text-gray-800">
                              {comment.text}
                            </p>
                          )}

                          {isSpoilerComment && isRevealed && (
                            <button
                              type="button"
                              onClick={() => toggleSpoilerReveal(comment.id)}
                              className="text-xs text-gray-400 hover:text-gray-600 mt-1 transition-colors"
                            >
                              Ocultar spoiler
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Comment Form */}
                <form
                  onSubmit={handlePostComment}
                  className="space-y-3 border-t border-gray-200 pt-4"
                >
                  <div className="flex flex-col gap-1">
                    <label
                      htmlFor="comment-text"
                      className="text-sm font-medium text-gray-700"
                    >
                      Tu comentario
                    </label>
                    <textarea
                      id="comment-text"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      placeholder="Escribe tu comentario..."
                      rows={3}
                      className="rounded-md border border-gray-300 px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="is-spoiler"
                      checked={isSpoiler}
                      onChange={(e) => setIsSpoiler(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <label
                      htmlFor="is-spoiler"
                      className="text-sm text-gray-700"
                    >
                      Tiene spoilers
                    </label>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={!commentText.trim() || submittingComment}
                      className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {submittingComment
                        ? "Publicando..."
                        : "Publicar comentario"}
                    </button>
                  </div>
                </form>
              </section>
            </>
          )}

          {/* Error State */}
          {!loading && !club && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
              <p className="text-lg font-medium text-gray-900 mb-2">
                Club no encontrado
              </p>
              <p className="text-sm text-gray-500">
                No se pudo cargar la información del club.
              </p>
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
