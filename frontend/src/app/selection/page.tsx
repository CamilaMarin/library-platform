"use client";

import { useEffect, useState, useCallback } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { apiGet, apiPost, ApiError } from "@/lib/api-client";
import type { FamilyGroup, Draw, NextPicker, Book } from "@/types";

interface DrawFilters {
  genre: string;
  max_pages: string;
  unread_only: boolean;
}

interface GroupDrawState {
  nextPicker: NextPicker | null;
  draws: Draw[];
  loadingPicker: boolean;
  loadingDraws: boolean;
}

const inputStyle: React.CSSProperties = {
  borderColor: "var(--color-border)",
  background: "var(--color-cream)",
  color: "var(--color-ink)",
};

export default function SelectionPage() {
  const [groups, setGroups] = useState<FamilyGroup[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [groupStates, setGroupStates] = useState<Record<string, GroupDrawState>>({});
  const [activeDrawForm, setActiveDrawForm] = useState<string | null>(null);
  const [filters, setFilters] = useState<DrawFilters>({ genre: "", max_pages: "", unread_only: false });
  const [drawingGroupId, setDrawingGroupId] = useState<string | null>(null);
  const [drawResult, setDrawResult] = useState<{ groupId: string; book: Book } | null>(null);
  const [noMatchError, setNoMatchError] = useState<string | null>(null);

  const fetchGroups = useCallback(async () => {
    setLoadingGroups(true);
    try {
      const data = await apiGet<FamilyGroup[]>("/groups");
      setGroups(data);
    } catch {
      setGroups([]);
    } finally {
      setLoadingGroups(false);
    }
  }, []);

  const fetchNextPicker = useCallback(async (groupId: string) => {
    setGroupStates((prev) => ({
      ...prev,
      [groupId]: { ...prev[groupId], loadingPicker: true },
    }));
    try {
      const picker = await apiGet<NextPicker>(`/groups/${groupId}/draws/next-picker`);
      setGroupStates((prev) => ({
        ...prev,
        [groupId]: { ...prev[groupId], nextPicker: picker, loadingPicker: false },
      }));
    } catch {
      setGroupStates((prev) => ({
        ...prev,
        [groupId]: { ...prev[groupId], nextPicker: null, loadingPicker: false },
      }));
    }
  }, []);

  const fetchDrawHistory = useCallback(async (groupId: string) => {
    setGroupStates((prev) => ({
      ...prev,
      [groupId]: { ...prev[groupId], loadingDraws: true },
    }));
    try {
      const draws = await apiGet<Draw[]>(`/groups/${groupId}/draws`);
      setGroupStates((prev) => ({
        ...prev,
        [groupId]: { ...prev[groupId], draws, loadingDraws: false },
      }));
    } catch {
      setGroupStates((prev) => ({
        ...prev,
        [groupId]: { ...prev[groupId], draws: [], loadingDraws: false },
      }));
    }
  }, []);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  useEffect(() => {
    if (groups.length > 0) {
      const initial: Record<string, GroupDrawState> = {};
      groups.forEach((g) => {
        initial[g.id] = { nextPicker: null, draws: [], loadingPicker: true, loadingDraws: true };
      });
      setGroupStates(initial);
      groups.forEach((g) => {
        fetchNextPicker(g.id);
        fetchDrawHistory(g.id);
      });
    }
  }, [groups, fetchNextPicker, fetchDrawHistory]);

  const handleDraw = async (groupId: string) => {
    setDrawingGroupId(groupId);
    setDrawResult(null);
    setNoMatchError(null);

    const body: Record<string, unknown> = { participant_ids: [] };
    if (filters.genre.trim()) body.genre = filters.genre.trim();
    if (filters.max_pages.trim()) body.max_pages = parseInt(filters.max_pages, 10);
    if (filters.unread_only) body.unread_only = true;

    try {
      const draw = await apiPost<Draw>(`/groups/${groupId}/draws`, body);

      if (draw.result_book_id) {
        try {
          const book = await apiGet<Book>(`/books/${draw.result_book_id}`);
          setDrawResult({ groupId, book });
        } catch {
          setDrawResult({
            groupId,
            book: {
              id: draw.result_book_id,
              title: "Libro seleccionado",
              author: "Autor desconocido",
              genres: [],
              description: null,
              pages: null,
              isbn: null,
              created_at: "",
            },
          });
        }
      }

      fetchDrawHistory(groupId);
      fetchNextPicker(groupId);
      setActiveDrawForm(null);
      setFilters({ genre: "", max_pages: "", unread_only: false });
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
        if (
          detail.toLowerCase().includes("no matching") ||
          detail.toLowerCase().includes("no books") ||
          err.status === 404
        ) {
          setNoMatchError("No se encontraron libros que coincidan con los filtros.");
        }
      }
    } finally {
      setDrawingGroupId(null);
    }
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  const formatFilters = (drawFilters: Record<string, unknown>) => {
    const parts: string[] = [];
    if (drawFilters.genre) parts.push(`Género: ${drawFilters.genre}`);
    if (drawFilters.max_pages) parts.push(`Máx. páginas: ${drawFilters.max_pages}`);
    if (drawFilters.unread_only) parts.push("Solo no leídos");
    return parts.length > 0 ? parts.join(", ") : "Sin filtros";
  };

  return (
    <ProtectedRoute>
      <Navigation />
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1
            className="text-2xl font-bold mb-6"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--color-walnut)",
            }}
          >
            Selección de Lectura
          </h1>

          {loadingGroups && <Skeleton variant="card" count={2} />}

          {!loadingGroups && groups.length === 0 && (
            <div
              className="rounded-lg p-8 text-center"
              style={{ background: "var(--color-cream)", border: "1px solid var(--color-border)" }}
            >
              <p className="text-base font-medium" style={{ color: "var(--color-walnut)" }}>
                Únete a un grupo para comenzar a sortear.
              </p>
            </div>
          )}

          {!loadingGroups && groups.length > 0 && (
            <div className="space-y-6">
              {groups.map((group) => {
                const state = groupStates[group.id];
                if (!state) return null;

                return (
                  <section
                    key={group.id}
                    className="rounded-lg overflow-hidden"
                    style={{
                      background: "var(--color-cream)",
                      border: "1px solid var(--color-border)",
                      boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                    }}
                  >
                    {/* Group Header */}
                    <div
                      className="px-5 py-4"
                      style={{ borderBottom: "1px solid var(--color-border)" }}
                    >
                      <h2
                        className="text-lg font-semibold"
                        style={{
                          fontFamily: "var(--font-playfair), Georgia, serif",
                          color: "var(--color-walnut)",
                        }}
                      >
                        {group.name}
                      </h2>

                      {state.loadingPicker ? (
                        <Skeleton variant="text" count={1} />
                      ) : (
                        <p className="text-sm mt-1" style={{ color: "var(--color-ink-faint)" }}>
                          {state.nextPicker?.next_picker_user_id
                            ? `Próximo turno: ${state.nextPicker.next_picker_user_id}`
                            : "Sin turno asignado"}
                        </p>
                      )}

                      <button
                        type="button"
                        onClick={() => {
                          setActiveDrawForm(activeDrawForm === group.id ? null : group.id);
                          setDrawResult(null);
                          setNoMatchError(null);
                          setFilters({ genre: "", max_pages: "", unread_only: false });
                        }}
                        className="mt-3 rounded-full px-4 py-2 text-sm font-medium transition-colors"
                        style={{ background: "var(--color-brass)", color: "var(--color-cream)" }}
                        onMouseEnter={(e) =>
                          ((e.currentTarget as HTMLButtonElement).style.background =
                            "var(--color-brass-lt)")
                        }
                        onMouseLeave={(e) =>
                          ((e.currentTarget as HTMLButtonElement).style.background =
                            "var(--color-brass)")
                        }
                      >
                        ✦ Nuevo sorteo
                      </button>
                    </div>

                    {/* Draw Form */}
                    {activeDrawForm === group.id && (
                      <div
                        className="px-5 py-4"
                        style={{
                          background: "var(--color-parchment)",
                          borderBottom: "1px solid var(--color-border)",
                        }}
                      >
                        <h3
                          className="text-sm font-medium mb-3"
                          style={{ color: "var(--color-ink-soft)" }}
                        >
                          Filtros (opcionales)
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                          <div className="flex flex-col gap-1">
                            <label
                              htmlFor={`genre-${group.id}`}
                              className="text-sm font-medium"
                              style={{ color: "var(--color-ink-soft)" }}
                            >
                              Género
                            </label>
                            <input
                              id={`genre-${group.id}`}
                              type="text"
                              value={filters.genre}
                              onChange={(e) =>
                                setFilters((prev) => ({ ...prev, genre: e.target.value }))
                              }
                              placeholder="Ej: Ficción"
                              className="rounded-md border px-3 py-2 text-sm focus:outline-none"
                              style={inputStyle}
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label
                              htmlFor={`max-pages-${group.id}`}
                              className="text-sm font-medium"
                              style={{ color: "var(--color-ink-soft)" }}
                            >
                              Máx. páginas
                            </label>
                            <input
                              id={`max-pages-${group.id}`}
                              type="number"
                              value={filters.max_pages}
                              onChange={(e) =>
                                setFilters((prev) => ({ ...prev, max_pages: e.target.value }))
                              }
                              placeholder="Ej: 300"
                              min="1"
                              className="rounded-md border px-3 py-2 text-sm focus:outline-none"
                              style={inputStyle}
                            />
                          </div>
                          <div className="flex items-end gap-2 pb-1">
                            <input
                              id={`unread-${group.id}`}
                              type="checkbox"
                              checked={filters.unread_only}
                              onChange={(e) =>
                                setFilters((prev) => ({ ...prev, unread_only: e.target.checked }))
                              }
                              className="h-4 w-4 rounded"
                              style={{ accentColor: "var(--color-teak)" }}
                            />
                            <label
                              htmlFor={`unread-${group.id}`}
                              className="text-sm font-medium"
                              style={{ color: "var(--color-ink-soft)" }}
                            >
                              Solo no leídos
                            </label>
                          </div>
                        </div>
                        <div className="flex gap-3">
                          <button
                            type="button"
                            onClick={() => handleDraw(group.id)}
                            disabled={drawingGroupId === group.id}
                            className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            style={{ background: "var(--color-reading)", color: "var(--color-cream)" }}
                          >
                            {drawingGroupId === group.id ? "Sorteando..." : "Sortear"}
                          </button>
                          <button
                            type="button"
                            onClick={() => { setActiveDrawForm(null); setNoMatchError(null); }}
                            className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                            style={{
                              border: "1px solid var(--color-border)",
                              color: "var(--color-ink-soft)",
                              background: "transparent",
                            }}
                            onMouseEnter={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background =
                                "var(--color-cream)")
                            }
                            onMouseLeave={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background =
                                "transparent")
                            }
                          >
                            Cancelar
                          </button>
                        </div>

                        {noMatchError && (
                          <p
                            className="mt-3 text-sm rounded-md px-3 py-2"
                            style={{
                              color: "var(--color-brass-dark, #8A6620)",
                              background: "#FDF6E3",
                              border: "1px solid var(--color-brass)",
                            }}
                          >
                            {noMatchError}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Draw Result */}
                    {drawResult && drawResult.groupId === group.id && (
                      <div
                        className="px-5 py-4"
                        style={{
                          background: "#EDF7F0",
                          borderBottom: "1px solid var(--color-border)",
                        }}
                      >
                        <p
                          className="text-sm font-medium"
                          style={{ color: "var(--color-reading)" }}
                        >
                          ✓ Libro seleccionado:{" "}
                          <span
                            style={{
                              fontFamily: "var(--font-playfair), Georgia, serif",
                              color: "var(--color-walnut)",
                            }}
                          >
                            {drawResult.book.title}
                          </span>{" "}
                          por {drawResult.book.author}
                        </p>
                      </div>
                    )}

                    {/* Draw History */}
                    <div className="px-5 py-4">
                      <h3
                        className="text-sm font-medium mb-3"
                        style={{ color: "var(--color-ink-soft)" }}
                      >
                        Historial de sorteos
                      </h3>
                      {state.loadingDraws ? (
                        <Skeleton variant="list" count={3} />
                      ) : state.draws.length === 0 ? (
                        <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                          No hay sorteos previos
                        </p>
                      ) : (
                        <ul className="space-y-2">
                          {[...state.draws]
                            .sort(
                              (a, b) =>
                                new Date(b.timestamp).getTime() -
                                new Date(a.timestamp).getTime()
                            )
                            .map((draw) => (
                              <li
                                key={draw.id}
                                className="rounded-md px-4 py-3"
                                style={{
                                  background: "var(--color-parchment)",
                                  border: "1px solid var(--color-border)",
                                }}
                              >
                                <div className="flex items-center justify-between">
                                  <span
                                    className="text-sm"
                                    style={{ color: "var(--color-ink)" }}
                                  >
                                    {formatDate(draw.timestamp)}
                                  </span>
                                  {draw.result_book_id && (
                                    <span
                                      className="text-xs"
                                      style={{ color: "var(--color-ink-faint)" }}
                                    >
                                      Libro: {draw.result_book_id.slice(0, 8)}…
                                    </span>
                                  )}
                                </div>
                                <p
                                  className="text-xs mt-1"
                                  style={{ color: "var(--color-ink-faint)" }}
                                >
                                  {formatFilters(draw.filters)}
                                </p>
                              </li>
                            ))}
                        </ul>
                      )}
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
