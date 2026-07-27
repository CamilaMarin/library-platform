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

export default function SelectionPage() {
  const [groups, setGroups] = useState<FamilyGroup[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [groupStates, setGroupStates] = useState<Record<string, GroupDrawState>>({});
  const [activeDrawForm, setActiveDrawForm] = useState<string | null>(null);
  const [filters, setFilters] = useState<DrawFilters>({ genre: "", max_pages: "", unread_only: false });
  const [drawingGroupId, setDrawingGroupId] = useState<string | null>(null);
  const [drawResult, setDrawResult] = useState<{ groupId: string; book: Book } | null>(null);
  const [noMatchError, setNoMatchError] = useState<string | null>(null);

  // Fetch groups
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

  // Fetch next picker for a group
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

  // Fetch draw history for a group
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

  // When groups are loaded, fetch next picker and draw history for each
  useEffect(() => {
    if (groups.length > 0) {
      const initial: Record<string, GroupDrawState> = {};
      groups.forEach((g) => {
        initial[g.id] = {
          nextPicker: null,
          draws: [],
          loadingPicker: true,
          loadingDraws: true,
        };
      });
      setGroupStates(initial);

      groups.forEach((g) => {
        fetchNextPicker(g.id);
        fetchDrawHistory(g.id);
      });
    }
  }, [groups, fetchNextPicker, fetchDrawHistory]);

  // Handle draw trigger
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

      // Refresh draw history and picker
      fetchDrawHistory(groupId);
      fetchNextPicker(groupId);
      setActiveDrawForm(null);
      setFilters({ genre: "", max_pages: "", unread_only: false });
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
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

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Format filters for display
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
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Selección de Lectura
          </h1>

          {/* Loading State */}
          {loadingGroups && <Skeleton variant="card" count={2} />}

          {/* Empty State - No groups */}
          {!loadingGroups && groups.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
              <p className="text-lg font-medium text-gray-900 mb-2">
                Únete a un grupo para comenzar a sortear.
              </p>
            </div>
          )}

          {/* Groups with draw functionality */}
          {!loadingGroups && groups.length > 0 && (
            <div className="space-y-6">
              {groups.map((group) => {
                const state = groupStates[group.id];
                if (!state) return null;

                return (
                  <section
                    key={group.id}
                    className="rounded-lg border border-gray-200 bg-white shadow-sm"
                  >
                    {/* Group Header */}
                    <div className="px-5 py-4 border-b border-gray-100">
                      <h2 className="text-lg font-semibold text-gray-900">
                        {group.name}
                      </h2>

                      {/* Next Picker */}
                      {state.loadingPicker ? (
                        <Skeleton variant="text" count={1} />
                      ) : (
                        <p className="text-sm text-gray-600 mt-1">
                          {state.nextPicker?.next_picker_user_id
                            ? `Próximo turno: ${state.nextPicker.next_picker_user_id}`
                            : "Sin turno asignado"}
                        </p>
                      )}

                      {/* New Draw Button */}
                      <button
                        type="button"
                        onClick={() => {
                          setActiveDrawForm(activeDrawForm === group.id ? null : group.id);
                          setDrawResult(null);
                          setNoMatchError(null);
                          setFilters({ genre: "", max_pages: "", unread_only: false });
                        }}
                        className="mt-3 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
                      >
                        Nuevo sorteo
                      </button>
                    </div>

                    {/* Draw Form */}
                    {activeDrawForm === group.id && (
                      <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
                        <h3 className="text-sm font-medium text-gray-700 mb-3">
                          Filtros (opcionales)
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                          <div className="flex flex-col gap-1">
                            <label
                              htmlFor={`genre-${group.id}`}
                              className="text-sm font-medium text-gray-700"
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
                              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label
                              htmlFor={`max-pages-${group.id}`}
                              className="text-sm font-medium text-gray-700"
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
                              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <label
                              htmlFor={`unread-${group.id}`}
                              className="text-sm font-medium text-gray-700"
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
                            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {drawingGroupId === group.id ? "Sorteando..." : "Sortear"}
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setActiveDrawForm(null);
                              setNoMatchError(null);
                            }}
                            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            Cancelar
                          </button>
                        </div>

                        {/* No match error */}
                        {noMatchError && (
                          <p className="mt-3 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
                            {noMatchError}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Draw Result */}
                    {drawResult && drawResult.groupId === group.id && (
                      <div className="px-5 py-4 border-b border-gray-100 bg-green-50">
                        <p className="text-sm font-medium text-green-800">
                          Libro seleccionado: {drawResult.book.title} por {drawResult.book.author}
                        </p>
                      </div>
                    )}

                    {/* Draw History */}
                    <div className="px-5 py-4">
                      <h3 className="text-sm font-medium text-gray-700 mb-3">
                        Historial de sorteos
                      </h3>
                      {state.loadingDraws ? (
                        <Skeleton variant="list" count={3} />
                      ) : state.draws.length === 0 ? (
                        <p className="text-sm text-gray-500">No hay sorteos previos</p>
                      ) : (
                        <ul className="space-y-2">
                          {[...state.draws]
                            .sort(
                              (a, b) =>
                                new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
                            )
                            .map((draw) => (
                              <li
                                key={draw.id}
                                className="rounded-md border border-gray-100 bg-gray-50 px-4 py-3"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="text-sm text-gray-900">
                                    {formatDate(draw.timestamp)}
                                  </span>
                                  {draw.result_book_id && (
                                    <span className="text-xs text-gray-500">
                                      Libro: {draw.result_book_id.slice(0, 8)}…
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-gray-500 mt-1">
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
