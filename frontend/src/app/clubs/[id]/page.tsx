"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { useToast } from "@/context/toast-context";
import { useAuth } from "@/context/auth-context";
import { apiGet, apiPost, ApiError } from "@/lib/api-client";

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

export default function ClubDetailPage() {
  const params = useParams();
  const clubId = params.id as string;
  const { user } = useAuth();
  const { showToast } = useToast();

  const [club, setClub] = useState<ClubDetail | null>(null);
  const [members, setMembers] = useState<ClubMember[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  const [commentText, setCommentText] = useState("");
  const [isSpoiler, setIsSpoiler] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);

  const [showSetBookForm, setShowSetBookForm] = useState(false);
  const [availableBooks, setAvailableBooks] = useState<BookOption[]>([]);
  const [selectedBookId, setSelectedBookId] = useState("");
  const [settingBook, setSettingBook] = useState(false);
  const [revealedSpoilers, setRevealedSpoilers] = useState<Set<string>>(new Set());
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
          const book = await apiGet<{ id: string; title: string; author: string }>(
            `/books/${clubData.active_book_id}`
          );
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
      await apiPost(`/clubs/${clubId}/active-book`, { book_id: selectedBookId });
      setClub((prev) => (prev ? { ...prev, active_book_id: selectedBookId } : prev));
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
      const books = await apiGet<BookOption[]>(`/clubs/${clubId}/available-books`);
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
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          {loading && <Skeleton variant="card" count={3} />}

          {!loading && club && (
            <>
              {/* Header */}
              <div className="mb-6">
                <h1
                  className="text-2xl font-bold"
                  style={{
                    fontFamily: "var(--font-playfair), Georgia, serif",
                    color: "var(--color-walnut)",
                  }}
                >
                  {club.name}
                </h1>
                {club.description && (
                  <p
                    className="text-sm mt-1"
                    style={{ color: "var(--color-ink-faint)" }}
                  >
                    {club.description}
                  </p>
                )}
              </div>

              {/* Active Book */}
              <section
                className="mb-6 rounded-lg p-5"
                style={{
                  background: "var(--color-cream)",
                  border: "1px solid var(--color-border)",
                  boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                }}
              >
                <h2
                  className="text-base font-semibold mb-3"
                  style={{ color: "var(--color-walnut)" }}
                >
                  📖 Libro activo
                </h2>

                {club.active_book_id ? (
                  <p
                    className="text-sm italic"
                    style={{
                      fontFamily: "var(--font-playfair), Georgia, serif",
                      color: "var(--color-ink)",
                    }}
                  >
                    {activeBookTitle || club.active_book_id}
                  </p>
                ) : (
                  <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                    No hay un libro activo actualmente.
                  </p>
                )}

                {isOwner && !showSetBookForm && (
                  <button
                    type="button"
                    onClick={handleOpenSetBookForm}
                    className="mt-3 rounded-full px-4 py-2 text-sm font-medium transition-colors"
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
                    Establecer libro activo
                  </button>
                )}

                {isOwner && showSetBookForm && (
                  <form onSubmit={handleSetActiveBook} className="mt-4 space-y-3">
                    <div className="flex flex-col gap-1">
                      <label
                        htmlFor="select-active-book"
                        className="text-sm font-medium"
                        style={{ color: "var(--color-ink-soft)" }}
                      >
                        Seleccionar libro
                      </label>
                      <select
                        id="select-active-book"
                        value={selectedBookId}
                        onChange={(e) => setSelectedBookId(e.target.value)}
                        className="rounded-md border px-3 py-2 text-sm focus:outline-none"
                        style={{
                          borderColor: "var(--color-border)",
                          background: "var(--color-cream)",
                          color: "var(--color-ink)",
                        }}
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
                        className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
                        onMouseEnter={(e) => {
                          if (selectedBookId && !settingBook)
                            (e.currentTarget as HTMLButtonElement).style.background =
                              "var(--color-mahogany)";
                        }}
                        onMouseLeave={(e) => {
                          if (selectedBookId && !settingBook)
                            (e.currentTarget as HTMLButtonElement).style.background =
                              "var(--color-walnut)";
                        }}
                      >
                        {settingBook ? "Guardando..." : "Confirmar"}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowSetBookForm(false);
                          setSelectedBookId("");
                        }}
                        className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
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
                  </form>
                )}
              </section>

              {/* Members */}
              <section
                className="mb-6 rounded-lg p-5"
                style={{
                  background: "var(--color-cream)",
                  border: "1px solid var(--color-border)",
                  boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                }}
              >
                <h2
                  className="text-base font-semibold mb-3"
                  style={{ color: "var(--color-walnut)" }}
                >
                  👥 Miembros ({members.length})
                </h2>

                {members.length === 0 ? (
                  <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                    No hay miembros en este club.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {members.map((member) => (
                      <li
                        key={member.id}
                        className="flex items-center justify-between rounded-md px-3 py-2"
                        style={{ background: "var(--color-parchment)" }}
                      >
                        <span className="text-sm" style={{ color: "var(--color-ink-soft)" }}>
                          {member.name}
                        </span>
                        {member.role === "owner" && (
                          <span
                            className="text-xs font-medium rounded-full px-2 py-0.5"
                            style={{
                              background: "#FDF6E3",
                              color: "var(--color-brass)",
                              border: "1px solid var(--color-brass)",
                            }}
                          >
                            Propietario
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              {/* Comments */}
              <section
                className="rounded-lg p-5"
                style={{
                  background: "var(--color-cream)",
                  border: "1px solid var(--color-border)",
                  boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                }}
              >
                <h2
                  className="text-base font-semibold mb-3"
                  style={{ color: "var(--color-walnut)" }}
                >
                  💬 Comentarios
                </h2>

                {comments.length === 0 ? (
                  <p
                    className="text-sm mb-4"
                    style={{ color: "var(--color-ink-faint)" }}
                  >
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
                          className="rounded-md p-3"
                          style={{ background: "var(--color-parchment)" }}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span
                              className="text-xs font-medium"
                              style={{ color: "var(--color-ink-soft)" }}
                            >
                              {getMemberName(comment.user_id)}
                            </span>
                            <span
                              className="text-xs"
                              style={{ color: "var(--color-ink-faint)" }}
                            >
                              {formatDate(comment.created_at)}
                            </span>
                          </div>

                          {isSpoilerComment && (
                            <span
                              className="inline-block text-xs font-medium rounded px-2 py-0.5 mb-1"
                              style={{
                                background: "#FDF6E3",
                                color: "var(--color-brass-dark, #8A6620)",
                              }}
                            >
                              ⚠️ Contiene spoilers
                            </span>
                          )}

                          {isSpoilerComment && !isRevealed ? (
                            <button
                              type="button"
                              onClick={() => toggleSpoilerReveal(comment.id)}
                              className="block w-full text-left text-sm italic transition-colors"
                              style={{ color: "var(--color-ink-faint)" }}
                              onMouseEnter={(e) =>
                                ((e.currentTarget as HTMLButtonElement).style.color =
                                  "var(--color-ink-soft)")
                              }
                              onMouseLeave={(e) =>
                                ((e.currentTarget as HTMLButtonElement).style.color =
                                  "var(--color-ink-faint)")
                              }
                            >
                              Haz clic para revelar el contenido con spoilers
                            </button>
                          ) : (
                            <p className="text-sm" style={{ color: "var(--color-ink)" }}>
                              {comment.text}
                            </p>
                          )}

                          {isSpoilerComment && isRevealed && (
                            <button
                              type="button"
                              onClick={() => toggleSpoilerReveal(comment.id)}
                              className="text-xs mt-1 transition-colors"
                              style={{ color: "var(--color-ink-faint)" }}
                              onMouseEnter={(e) =>
                                ((e.currentTarget as HTMLButtonElement).style.color =
                                  "var(--color-ink-soft)")
                              }
                              onMouseLeave={(e) =>
                                ((e.currentTarget as HTMLButtonElement).style.color =
                                  "var(--color-ink-faint)")
                              }
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
                  className="space-y-3 pt-4"
                  style={{ borderTop: "1px solid var(--color-border)" }}
                >
                  <div className="flex flex-col gap-1">
                    <label
                      htmlFor="comment-text"
                      className="text-sm font-medium"
                      style={{ color: "var(--color-ink-soft)" }}
                    >
                      Tu comentario
                    </label>
                    <textarea
                      id="comment-text"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      placeholder="Escribe tu comentario..."
                      rows={3}
                      className="rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
                      style={{
                        borderColor: "var(--color-border)",
                        background: "var(--color-cream)",
                        color: "var(--color-ink)",
                      }}
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="is-spoiler"
                      checked={isSpoiler}
                      onChange={(e) => setIsSpoiler(e.target.checked)}
                      className="h-4 w-4 rounded"
                      style={{ accentColor: "var(--color-teak)" }}
                    />
                    <label
                      htmlFor="is-spoiler"
                      className="text-sm"
                      style={{ color: "var(--color-ink-soft)" }}
                    >
                      Tiene spoilers
                    </label>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={!commentText.trim() || submittingComment}
                      className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
                      onMouseEnter={(e) => {
                        if (commentText.trim() && !submittingComment)
                          (e.currentTarget as HTMLButtonElement).style.background =
                            "var(--color-mahogany)";
                      }}
                      onMouseLeave={(e) => {
                        if (commentText.trim() && !submittingComment)
                          (e.currentTarget as HTMLButtonElement).style.background =
                            "var(--color-walnut)";
                      }}
                    >
                      {submittingComment ? "Publicando..." : "Publicar comentario"}
                    </button>
                  </div>
                </form>
              </section>
            </>
          )}

          {/* Error / Not Found */}
          {!loading && !club && (
            <div
              className="rounded-lg p-8 text-center"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
              }}
            >
              <p
                className="text-base font-medium mb-2"
                style={{ color: "var(--color-walnut)" }}
              >
                Club no encontrado
              </p>
              <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                No se pudo cargar la información del club.
              </p>
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
