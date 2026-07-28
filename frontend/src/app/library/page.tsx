"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { LayoutList, Rows3 } from "lucide-react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { InputField } from "@/components/input-field";
import { SelectField } from "@/components/select-field";
import { CopyStatusBadge } from "@/components/copy-status-badge";
import { LoanForm } from "@/components/loan-form";
import { BookShelf } from "@/components/book-shelf";
import { useToast } from "@/context/toast-context";
import { useAuth } from "@/context/auth-context";
import { apiGet, apiPost, apiDelete, apiPut, ApiError } from "@/lib/api-client";
import type {
  Book,
  Copy,
  CopyWithLoanStatus,
  GroupMember,
  FamilyGroup,
  BookReadingStatus,
  ReadingStatusValue,
  StatusMap,
} from "@/types";
import { READING_STATUS_LABELS, SHELF_ORDER } from "@/types";

const PAGE_SIZE = 20;
const VIEW_MODE_KEY = "entrelineas_library_view";

interface AddBookFormState {
  title: string;
  author: string;
  isbn: string;
  genres: string;
  description: string;
  pages: string;
  initialCopyFormat: string;
}

const initialFormState: AddBookFormState = {
  title: "",
  author: "",
  isbn: "",
  genres: "",
  description: "",
  pages: "",
  initialCopyFormat: "none",
};

export default function LibraryPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addBookForm, setAddBookForm] = useState<AddBookFormState>(initialFormState);
  const [addBookErrors, setAddBookErrors] = useState<Record<string, string>>({});
  const [addBookSubmitting, setAddBookSubmitting] = useState(false);
  const [addCopyBookId, setAddCopyBookId] = useState<string | null>(null);
  const [addCopyFormat, setAddCopyFormat] = useState("physical");
  const [addCopySubmitting, setAddCopySubmitting] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { showToast } = useToast();
  const { user } = useAuth();

  // Loan state
  const [expandedBookId, setExpandedBookId] = useState<string | null>(null);
  const [bookCopies, setBookCopies] = useState<Record<string, CopyWithLoanStatus[]>>({});
  const [loadingCopies, setLoadingCopies] = useState<string | null>(null);
  const [lendCopyId, setLendCopyId] = useState<string | null>(null);
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([]);
  const [loadingLendData, setLoadingLendData] = useState(false);

  // View mode — list | shelf, persisted in localStorage
  const [viewMode, setViewMode] = useState<"list" | "shelf">("list");

  // Reading statuses map: book_id → status
  const [statusMap, setStatusMap] = useState<StatusMap>({});

  // ── Load view preference from localStorage ──────────────────────────────
  useEffect(() => {
    const saved = localStorage.getItem(VIEW_MODE_KEY);
    if (saved === "shelf" || saved === "list") setViewMode(saved);
  }, []);

  const toggleViewMode = () => {
    const next = viewMode === "list" ? "shelf" : "list";
    setViewMode(next);
    localStorage.setItem(VIEW_MODE_KEY, next);
  };

  // ── Fetch books + statuses in parallel ──────────────────────────────────
  const fetchBooks = useCallback(async (query?: string) => {
    setLoading(true);
    try {
      const path = query ? `/books?query=${encodeURIComponent(query)}` : "/books";
      const [booksData, statusesData] = await Promise.all([
        apiGet<Book[]>(path),
        apiGet<BookReadingStatus[]>("/books/statuses").catch(() => [] as BookReadingStatus[]),
      ]);
      setBooks(booksData);
      const map: StatusMap = {};
      statusesData.forEach((s) => { map[s.book_id] = s.status; });
      setStatusMap(map);
      setVisibleCount(PAGE_SIZE);
    } catch {
      setBooks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchBooks(); }, [fetchBooks]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchBooks(value || undefined), 300);
  };

  useEffect(() => {
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, []);

  // ── Reading status change handler ────────────────────────────────────────
  const handleStatusChange = useCallback(
    async (bookId: string, status: ReadingStatusValue | null) => {
      // Optimistic update
      setStatusMap((prev) => {
        const next = { ...prev };
        if (status === null) delete next[bookId];
        else next[bookId] = status;
        return next;
      });
      try {
        if (status === null) {
          await apiDelete(`/books/${bookId}/status`);
        } else {
          await apiPut(`/books/${bookId}/status`, { status });
        }
      } catch {
        showToast("Error al actualizar estado", "error");
        // Revert on error
        fetchBooks(searchTerm || undefined);
      }
    },
    [showToast, fetchBooks, searchTerm]
  );

  // ── Book form handlers ───────────────────────────────────────────────────
  const handleAddBookChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setAddBookForm((prev) => ({ ...prev, [name]: value }));
    if (addBookErrors[name]) {
      setAddBookErrors((prev) => { const n = { ...prev }; delete n[name]; return n; });
    }
  };

  const handleAddBookSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};
    if (!addBookForm.title.trim()) errors.title = "El título es obligatorio";
    if (!addBookForm.author.trim()) errors.author = "El autor es obligatorio";
    if (addBookForm.pages && isNaN(Number(addBookForm.pages)))
      errors.pages = "Debe ser un número válido";
    if (Object.keys(errors).length > 0) { setAddBookErrors(errors); return; }

    setAddBookSubmitting(true);
    setAddBookErrors({});
    try {
      const body: Record<string, unknown> = {
        title: addBookForm.title.trim(),
        author: addBookForm.author.trim(),
      };
      if (addBookForm.isbn.trim()) body.isbn = addBookForm.isbn.trim();
      if (addBookForm.genres.trim())
        body.genres = addBookForm.genres.split(",").map((g) => g.trim()).filter(Boolean);
      if (addBookForm.description.trim()) body.description = addBookForm.description.trim();
      if (addBookForm.pages.trim()) body.pages = Number(addBookForm.pages);
      body.initial_copy_format = addBookForm.initialCopyFormat;

      const newBook = await apiPost<Book>("/books", body);
      setBooks((prev) => [newBook, ...prev]);

      // If created without a copy, the backend auto-assigns want_to_read.
      // Reflect that immediately in the local statusMap so shelf view is
      // consistent without requiring a page refresh.
      if (!addBookForm.initialCopyFormat || addBookForm.initialCopyFormat === "none") {
        setStatusMap((prev) => ({ ...prev, [newBook.id]: "want_to_read" }));
      }

      setAddBookForm(initialFormState);
      setShowAddForm(false);
      showToast("Libro agregado exitosamente", "success");
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === "object")
        setAddBookErrors(err.detail as Record<string, string>);
      else if (err instanceof ApiError && typeof err.detail === "string")
        setAddBookErrors({ _general: err.detail });
    } finally {
      setAddBookSubmitting(false);
    }
  };

  const handleAddCopySubmit = async (bookId: string) => {
    setAddCopySubmitting(true);
    try {
      await apiPost<Copy>(`/copies/${addCopyFormat}`, { book_id: bookId });
      showToast("Copia agregada", "success");
      setAddCopyBookId(null);
      setAddCopyFormat("physical");
      if (expandedBookId === bookId) fetchCopiesForBook(bookId);
    } catch { showToast("Error al agregar copia", "error"); }
    finally { setAddCopySubmitting(false); }
  };

  const fetchCopiesForBook = useCallback(async (bookId: string) => {
    setLoadingCopies(bookId);
    try {
      const copies = await apiGet<CopyWithLoanStatus[]>(`/copies?book_id=${bookId}`);
      setBookCopies((prev) => ({ ...prev, [bookId]: copies }));
    } catch { setBookCopies((prev) => ({ ...prev, [bookId]: [] })); }
    finally { setLoadingCopies(null); }
  }, []);

  const handleToggleCopies = (bookId: string) => {
    if (expandedBookId === bookId) { setExpandedBookId(null); setLendCopyId(null); }
    else { setExpandedBookId(bookId); setLendCopyId(null); if (!bookCopies[bookId]) fetchCopiesForBook(bookId); }
  };

  const handleLendClick = async (copyId: string) => {
    setLoadingLendData(true);
    setLendCopyId(copyId);
    try {
      const groups = await apiGet<FamilyGroup[]>("/groups");
      if (groups.length > 0) {
        const members = await apiGet<GroupMember[]>(`/groups/${groups[0].id}/members`);
        setGroupMembers(members.filter((m) => m.user_id !== user?.id));
      } else { setGroupMembers([]); }
    } catch { setGroupMembers([]); }
    finally { setLoadingLendData(false); }
  };

  const handleLoanSuccess = () => {
    setLendCopyId(null);
    setGroupMembers([]);
    if (expandedBookId) fetchCopiesForBook(expandedBookId);
  };

  const visibleBooks = books.slice(0, visibleCount);
  const hasMore = visibleCount < books.length;

  // ── Shelf view: group books by status ────────────────────────────────────
  const shelves = SHELF_ORDER.map((s) => ({
    status: s,
    label: READING_STATUS_LABELS[s],
    books: books.filter((b) => statusMap[b.id] === s),
  }));
  const unclassified = books.filter((b) => !statusMap[b.id]);

  // ── Status badge for list view ───────────────────────────────────────────
  const STATUS_DOT: Record<ReadingStatusValue, string> = {
    reading:      "var(--color-reading)",
    read:         "var(--color-walnut)",
    want_to_read: "var(--color-teak)",
    dnf:          "var(--color-mahogany)",
  };

  return (
    <ProtectedRoute>
      <Navigation />
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">

          {/* ── Header ──────────────────────────────────────────────── */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1
                className="text-2xl font-bold"
                style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--color-walnut)" }}
              >
                Mi Biblioteca
              </h1>
              {viewMode === "shelf" && (
                <p className="text-sm mt-0.5" style={{ color: "var(--color-ink-faint)" }}>
                  Tus estantes, tal como los dejaste.
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {/* View toggle */}
              <button
                type="button"
                onClick={toggleViewMode}
                aria-label={viewMode === "list" ? "Cambiar a vista de estantes" : "Cambiar a vista de lista"}
                title={viewMode === "list" ? "Vista de estantes" : "Vista de lista"}
                className="rounded-lg p-2 transition-colors"
                style={{
                  background: "var(--color-cream)",
                  border: "1px solid var(--color-border)",
                  color: "var(--color-teak)",
                }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.borderColor = "var(--color-teak)")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.borderColor = "var(--color-border)")}
              >
                {viewMode === "list" ? <Rows3 size={16} /> : <LayoutList size={16} />}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm((p) => !p)}
                className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-mahogany)")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-walnut)")}
              >
                {showAddForm ? "Cancelar" : "Agregar libro"}
              </button>
            </div>
          </div>

          {/* ── Add Book Form (shared between both views) ────────────── */}
          {showAddForm && (
            <form onSubmit={handleAddBookSubmit} className="mb-6 rounded-lg p-5 space-y-4"
              style={{ background: "var(--color-cream)", border: "1px solid var(--color-border)", boxShadow: "0 1px 3px rgba(28,16,8,0.08)" }}>
              <h2 className="text-lg font-semibold" style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--color-walnut)" }}>
                Nuevo libro
              </h2>
              {addBookErrors._general && <p className="text-sm" style={{ color: "var(--color-leather)" }} role="alert">{addBookErrors._general}</p>}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <InputField label="Título" name="title" value={addBookForm.title} onChange={handleAddBookChange} error={addBookErrors.title} required placeholder="Título del libro" />
                <InputField label="Autor" name="author" value={addBookForm.author} onChange={handleAddBookChange} error={addBookErrors.author} required placeholder="Nombre del autor" />
                <InputField label="ISBN" name="isbn" value={addBookForm.isbn} onChange={handleAddBookChange} error={addBookErrors.isbn} placeholder="ISBN (opcional)" />
                <InputField label="Géneros" name="genres" value={addBookForm.genres} onChange={handleAddBookChange} error={addBookErrors.genres} placeholder="Ficción, Terror, Romance..." />
                <InputField label="Páginas" name="pages" type="number" value={addBookForm.pages} onChange={handleAddBookChange} error={addBookErrors.pages} placeholder="Número de páginas" />
                <SelectField label="Formato de copia" name="initialCopyFormat" value={addBookForm.initialCopyFormat}
                  onChange={(e) => setAddBookForm((p) => ({ ...p, initialCopyFormat: e.target.value }))}
                  options={[
                    { value: "none", label: "Sin copia (solo registrar)" },
                    { value: "physical", label: "Copia física" },
                  ]} />
              </div>
              <div className="flex flex-col gap-1">
                <label htmlFor="input-description" className="text-sm font-medium" style={{ color: "var(--color-ink-soft)" }}>Descripción</label>
                <textarea id="input-description" name="description" value={addBookForm.description} onChange={handleAddBookChange}
                  placeholder="Breve descripción del libro (opcional)" rows={3}
                  className="rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
                  style={{ borderColor: "var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }} />
              </div>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => { setShowAddForm(false); setAddBookForm(initialFormState); setAddBookErrors({}); }}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                  style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)", background: "transparent" }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-parchment)")}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}>
                  Cancelar
                </button>
                <button type="submit" disabled={addBookSubmitting}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
                  onMouseEnter={(e) => { if (!addBookSubmitting) (e.currentTarget as HTMLButtonElement).style.background = "var(--color-mahogany)"; }}
                  onMouseLeave={(e) => { if (!addBookSubmitting) (e.currentTarget as HTMLButtonElement).style.background = "var(--color-walnut)"; }}>
                  {addBookSubmitting ? "Guardando..." : "Guardar libro"}
                </button>
              </div>
            </form>
          )}

          {loading && <Skeleton variant="list" count={5} />}

          {!loading && books.length === 0 && (
            <div className="rounded-lg p-8 text-center" style={{ background: "var(--color-cream)", border: "1px solid var(--color-border)" }}>
              <p className="text-base font-medium mb-2" style={{ color: "var(--color-walnut)" }}>Tu biblioteca está vacía</p>
              <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>Agrega tu primer libro usando el botón &quot;Agregar libro&quot;.</p>
            </div>
          )}

          {/* ════════════════════════════════════════════════════════
              SHELF VIEW
          ════════════════════════════════════════════════════════ */}
          {!loading && books.length > 0 && viewMode === "shelf" && (
            <div>
              {/* Search hidden in shelf view — navigating by shelf is the point */}
              {shelves.map(({ status, label, books: shelfBooks }) => (
                <BookShelf
                  key={status}
                  label={label}
                  books={shelfBooks}
                  statusMap={statusMap}
                  shelfStatus={status}
                  onStatusChange={handleStatusChange}
                />
              ))}
              {/* Unclassified shelf */}
              <BookShelf
                label="Sin clasificar"
                books={unclassified}
                statusMap={statusMap}
                shelfStatus={null}
                onStatusChange={handleStatusChange}
              />
            </div>
          )}

          {/* ════════════════════════════════════════════════════════
              LIST VIEW
          ════════════════════════════════════════════════════════ */}
          {!loading && books.length > 0 && viewMode === "list" && (
            <div>
              {/* Search */}
              <div className="mb-6">
                <label htmlFor="search-books" className="sr-only">Buscar libros</label>
                <input id="search-books" type="text" value={searchTerm} onChange={handleSearchChange}
                  placeholder="Buscar por título o autor..."
                  className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none transition-colors"
                  style={{ borderColor: "var(--color-border)", background: "var(--color-cream)", color: "var(--color-ink)" }} />
              </div>

              <div className="space-y-3">
                {visibleBooks.map((book) => {
                  const bookStatus = statusMap[book.id] ?? null;
                  return (
                    <div key={book.id} className="rounded-lg px-5 py-4 transition-shadow"
                      style={{ background: "var(--color-cream)", border: "1px solid var(--color-border)", boxShadow: "0 1px 3px rgba(28,16,8,0.08)" }}
                      onMouseEnter={(e) => ((e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 12px -2px rgba(28,16,8,0.16)")}
                      onMouseLeave={(e) => ((e.currentTarget as HTMLDivElement).style.boxShadow = "0 1px 3px rgba(28,16,8,0.08)")}>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 min-w-0">
                          {/* Status dot */}
                          <span aria-hidden="true" style={{
                            width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                            background: bookStatus ? STATUS_DOT[bookStatus] : "var(--color-aged)",
                          }} />
                          <div className="min-w-0">
                            <h2 className="text-base font-semibold truncate"
                              style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--color-walnut)" }}>
                              {book.title}
                            </h2>
                            <p className="text-sm mt-0.5" style={{ color: "var(--color-ink-faint)" }}>{book.author}</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                          {/* Inline status selector */}
                          <select
                            aria-label={`Estado de ${book.title}`}
                            value={bookStatus ?? "none"}
                            onChange={(e) => {
                              const v = e.target.value;
                              handleStatusChange(book.id, v === "none" ? null : v as ReadingStatusValue);
                            }}
                            className="rounded-full text-xs px-2 py-1 focus:outline-none transition-colors"
                            style={{ borderColor: "var(--color-border)", background: "var(--color-parchment)", color: "var(--color-ink-soft)", border: "1px solid var(--color-border)" }}>
                            <option value="none">Sin estado</option>
                            <option value="reading">Leyendo</option>
                            <option value="want_to_read">Quiero leer</option>
                            <option value="read">Leído</option>
                            <option value="dnf">No terminado</option>
                          </select>

                          {addCopyBookId === book.id ? (
                            <div className="flex items-center gap-2">
                              <SelectField label="" name={`copy-format-${book.id}`} value={addCopyFormat}
                                onChange={(e) => setAddCopyFormat(e.target.value)}
                                options={[{ value: "physical", label: "Física" }]} />
                              <button type="button" disabled={addCopySubmitting} onClick={() => handleAddCopySubmit(book.id)}
                                className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                                style={{ background: "var(--color-reading)", color: "var(--color-cream)" }}>
                                {addCopySubmitting ? "..." : "Confirmar"}
                              </button>
                              <button type="button" onClick={() => { setAddCopyBookId(null); setAddCopyFormat("physical"); }}
                                className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors"
                                style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)", background: "transparent" }}>
                                Cancelar
                              </button>
                            </div>
                          ) : (
                            <>
                              <button type="button" onClick={() => handleToggleCopies(book.id)}
                                className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors"
                                style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)", background: "transparent" }}
                                onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-parchment)")}
                                onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}>
                                {expandedBookId === book.id ? "Ocultar copias" : "Ver copias"}
                              </button>
                              <button type="button" onClick={() => setAddCopyBookId(book.id)}
                                className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors"
                                style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)", background: "transparent" }}
                                onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-parchment)")}
                                onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}>
                                Agregar copia
                              </button>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Copies section */}
                      {expandedBookId === book.id && (
                        <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--color-border)" }}>
                          {loadingCopies === book.id && <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>Cargando copias...</p>}
                          {loadingCopies !== book.id && bookCopies[book.id]?.length === 0 && (
                            <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>No tienes copias de este libro.</p>
                          )}
                          {loadingCopies !== book.id && bookCopies[book.id]?.length > 0 && (
                            <div className="space-y-3">
                              {bookCopies[book.id].map((copy) => (
                                <div key={copy.id} className="flex items-center justify-between rounded-md px-3 py-2"
                                  style={{ background: "var(--color-parchment)" }}>
                                  <div className="flex items-center gap-3">
                                    <span className="text-xs font-medium uppercase" style={{ color: "var(--color-ink-soft)" }}>
                                      {copy.format === "physical" ? "Física" : "Digital"}
                                    </span>
                                    {copy.format === "physical" && (
                                      <CopyStatusBadge status={copy.loan_status} borrowerName={copy.active_loan?.borrower_name} loanDate={copy.active_loan?.loan_date} />
                                    )}
                                  </div>
                                  {copy.format === "physical" && copy.loan_status === "available" && lendCopyId !== copy.id && (
                                    <button type="button" onClick={() => handleLendClick(copy.id)} disabled={loadingLendData}
                                      className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                                      style={{ background: "var(--color-teak)", color: "var(--color-cream)" }}
                                      onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-mahogany)")}
                                      onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-teak)")}>
                                      Prestar
                                    </button>
                                  )}
                                </div>
                              ))}
                              {lendCopyId && bookCopies[book.id]?.some((c) => c.id === lendCopyId) && (
                                <div className="mt-3 rounded-md p-4" style={{ background: "#EDF7F0", border: "1px solid var(--color-reading)" }}>
                                  <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--color-walnut)" }}>Registrar préstamo</h3>
                                  {loadingLendData ? (
                                    <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>Cargando miembros del grupo...</p>
                                  ) : groupMembers.length === 0 ? (
                                    <div>
                                      <p className="text-sm mb-2" style={{ color: "var(--color-ink-soft)" }}>No tienes miembros en tu grupo para prestar.</p>
                                      <button type="button" onClick={() => { setLendCopyId(null); setGroupMembers([]); }}
                                        className="rounded-full px-3 py-1.5 text-xs font-medium"
                                        style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)", background: "transparent" }}>
                                        Cancelar
                                      </button>
                                    </div>
                                  ) : (
                                    <LoanForm copyId={lendCopyId} groupMembers={groupMembers} onSuccess={handleLoanSuccess} onCancel={() => { setLendCopyId(null); setGroupMembers([]); }} />
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}

                {hasMore && (
                  <div className="pt-4 text-center">
                    <button type="button" onClick={() => setVisibleCount((p) => p + PAGE_SIZE)}
                      className="rounded-full px-6 py-2 text-sm font-medium transition-colors"
                      style={{ border: "1px solid var(--color-border)", color: "var(--color-ink-soft)", background: "transparent" }}
                      onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-cream)")}
                      onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}>
                      Cargar más
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
