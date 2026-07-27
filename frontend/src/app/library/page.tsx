"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { InputField } from "@/components/input-field";
import { SelectField } from "@/components/select-field";
import { CopyStatusBadge } from "@/components/copy-status-badge";
import { LoanForm } from "@/components/loan-form";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPost, ApiError } from "@/lib/api-client";
import type { Book, Copy, CopyWithLoanStatus, GroupMember, FamilyGroup } from "@/types";

const PAGE_SIZE = 20;

interface AddBookFormState {
  title: string;
  author: string;
  isbn: string;
  genres: string;
  description: string;
  pages: string;
}

const initialFormState: AddBookFormState = {
  title: "",
  author: "",
  isbn: "",
  genres: "",
  description: "",
  pages: "",
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

  // Loan-related state
  const [expandedBookId, setExpandedBookId] = useState<string | null>(null);
  const [bookCopies, setBookCopies] = useState<Record<string, CopyWithLoanStatus[]>>({});
  const [loadingCopies, setLoadingCopies] = useState<string | null>(null);
  const [lendCopyId, setLendCopyId] = useState<string | null>(null);
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([]);
  const [loadingLendData, setLoadingLendData] = useState(false);

  const fetchBooks = useCallback(async (query?: string) => {
    setLoading(true);
    try {
      const path = query
        ? `/books?query=${encodeURIComponent(query)}`
        : "/books";
      const data = await apiGet<Book[]>(path);
      setBooks(data);
      setVisibleCount(PAGE_SIZE);
    } catch {
      setBooks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      fetchBooks(value || undefined);
    }, 300);
  };

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const handleAddBookChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setAddBookForm((prev) => ({ ...prev, [name]: value }));
    // Clear field error on change
    if (addBookErrors[name]) {
      setAddBookErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const handleAddBookSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Client-side validation
    const errors: Record<string, string> = {};
    if (!addBookForm.title.trim()) {
      errors.title = "El título es obligatorio";
    }
    if (!addBookForm.author.trim()) {
      errors.author = "El autor es obligatorio";
    }
    if (addBookForm.pages && isNaN(Number(addBookForm.pages))) {
      errors.pages = "Debe ser un número válido";
    }

    if (Object.keys(errors).length > 0) {
      setAddBookErrors(errors);
      return;
    }

    setAddBookSubmitting(true);
    setAddBookErrors({});

    try {
      const body: Record<string, unknown> = {
        title: addBookForm.title.trim(),
        author: addBookForm.author.trim(),
      };
      if (addBookForm.isbn.trim()) {
        body.isbn = addBookForm.isbn.trim();
      }
      if (addBookForm.genres.trim()) {
        body.genres = addBookForm.genres
          .split(",")
          .map((g) => g.trim())
          .filter(Boolean);
      }
      if (addBookForm.description.trim()) {
        body.description = addBookForm.description.trim();
      }
      if (addBookForm.pages.trim()) {
        body.pages = Number(addBookForm.pages);
      }

      const newBook = await apiPost<Book>("/books", body);
      setBooks((prev) => [newBook, ...prev]);
      setAddBookForm(initialFormState);
      setShowAddForm(false);
      showToast("Libro agregado exitosamente", "success");
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === "object") {
        setAddBookErrors(err.detail as Record<string, string>);
      } else if (err instanceof ApiError && typeof err.detail === "string") {
        setAddBookErrors({ _general: err.detail });
      }
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
      // Refresh copies if this book is expanded
      if (expandedBookId === bookId) {
        fetchCopiesForBook(bookId);
      }
    } catch {
      showToast("Error al agregar copia", "error");
    } finally {
      setAddCopySubmitting(false);
    }
  };

  // Fetch copies with loan status for a book
  const fetchCopiesForBook = useCallback(async (bookId: string) => {
    setLoadingCopies(bookId);
    try {
      const copies = await apiGet<CopyWithLoanStatus[]>(
        `/copies?book_id=${bookId}`
      );
      setBookCopies((prev) => ({ ...prev, [bookId]: copies }));
    } catch {
      setBookCopies((prev) => ({ ...prev, [bookId]: [] }));
    } finally {
      setLoadingCopies(null);
    }
  }, []);

  // Toggle copies view for a book
  const handleToggleCopies = (bookId: string) => {
    if (expandedBookId === bookId) {
      setExpandedBookId(null);
      setLendCopyId(null);
    } else {
      setExpandedBookId(bookId);
      setLendCopyId(null);
      if (!bookCopies[bookId]) {
        fetchCopiesForBook(bookId);
      }
    }
  };

  // Handle "Prestar" click — fetch group members and show form
  const handleLendClick = async (copyId: string) => {
    setLoadingLendData(true);
    setLendCopyId(copyId);
    try {
      // Fetch user's groups, then members from first group
      const groups = await apiGet<FamilyGroup[]>("/groups");
      if (groups.length > 0) {
        const members = await apiGet<GroupMember[]>(
          `/groups/${groups[0].id}/members`
        );
        setGroupMembers(members);
      } else {
        setGroupMembers([]);
      }
    } catch {
      setGroupMembers([]);
    } finally {
      setLoadingLendData(false);
    }
  };

  // Handle successful loan creation
  const handleLoanSuccess = () => {
    setLendCopyId(null);
    setGroupMembers([]);
    // Refresh copies for the expanded book
    if (expandedBookId) {
      fetchCopiesForBook(expandedBookId);
    }
  };

  // Handle loan form cancel
  const handleLoanCancel = () => {
    setLendCopyId(null);
    setGroupMembers([]);
  };

  const visibleBooks = books.slice(0, visibleCount);
  const hasMore = visibleCount < books.length;

  const handleLoadMore = () => {
    setVisibleCount((prev) => prev + PAGE_SIZE);
  };

  return (
    <ProtectedRoute>
      <Navigation />
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Mi Biblioteca</h1>
            <button
              type="button"
              onClick={() => setShowAddForm((prev) => !prev)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              {showAddForm ? "Cancelar" : "Agregar libro"}
            </button>
          </div>

          {/* Add Book Form */}
          {showAddForm && (
            <form
              onSubmit={handleAddBookSubmit}
              className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm space-y-4"
            >
              <h2 className="text-lg font-semibold text-gray-900">
                Nuevo libro
              </h2>

              {addBookErrors._general && (
                <p className="text-sm text-red-600" role="alert">
                  {addBookErrors._general}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <InputField
                  label="Título"
                  name="title"
                  value={addBookForm.title}
                  onChange={handleAddBookChange}
                  error={addBookErrors.title}
                  required
                  placeholder="Título del libro"
                />
                <InputField
                  label="Autor"
                  name="author"
                  value={addBookForm.author}
                  onChange={handleAddBookChange}
                  error={addBookErrors.author}
                  required
                  placeholder="Nombre del autor"
                />
                <InputField
                  label="ISBN"
                  name="isbn"
                  value={addBookForm.isbn}
                  onChange={handleAddBookChange}
                  error={addBookErrors.isbn}
                  placeholder="ISBN (opcional)"
                />
                <InputField
                  label="Géneros"
                  name="genres"
                  value={addBookForm.genres}
                  onChange={handleAddBookChange}
                  error={addBookErrors.genres}
                  placeholder="Ficción, Terror, Romance..."
                />
                <InputField
                  label="Páginas"
                  name="pages"
                  type="number"
                  value={addBookForm.pages}
                  onChange={handleAddBookChange}
                  error={addBookErrors.pages}
                  placeholder="Número de páginas"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label
                  htmlFor="input-description"
                  className="text-sm font-medium text-gray-700"
                >
                  Descripción
                </label>
                <textarea
                  id="input-description"
                  name="description"
                  value={addBookForm.description}
                  onChange={handleAddBookChange}
                  placeholder="Breve descripción del libro (opcional)"
                  rows={3}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setAddBookForm(initialFormState);
                    setAddBookErrors({});
                  }}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={addBookSubmitting}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {addBookSubmitting ? "Guardando..." : "Guardar libro"}
                </button>
              </div>
            </form>
          )}

          {/* Search */}
          <div className="mb-6">
            <label htmlFor="search-books" className="sr-only">
              Buscar libros
            </label>
            <input
              id="search-books"
              type="text"
              value={searchTerm}
              onChange={handleSearchChange}
              placeholder="Buscar por título o autor..."
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Loading State */}
          {loading && <Skeleton variant="list" count={5} />}

          {/* Empty State */}
          {!loading && books.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
              <p className="text-lg font-medium text-gray-900 mb-2">
                Tu biblioteca está vacía
              </p>
              <p className="text-sm text-gray-500">
                Agrega tu primer libro usando el botón &quot;Agregar libro&quot;
                para comenzar a construir tu colección.
              </p>
            </div>
          )}

          {/* Books List */}
          {!loading && books.length > 0 && (
            <div className="space-y-3">
              {visibleBooks.map((book) => (
                <div
                  key={book.id}
                  className="rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-gray-900">
                        {book.title}
                      </h2>
                      <p className="text-sm text-gray-500 mt-0.5">
                        {book.author}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {addCopyBookId === book.id ? (
                        <div className="flex items-center gap-2">
                          <SelectField
                            label=""
                            name={`copy-format-${book.id}`}
                            value={addCopyFormat}
                            onChange={(e) => setAddCopyFormat(e.target.value)}
                            options={[
                              { value: "physical", label: "Física" },
                              { value: "digital", label: "Digital" },
                            ]}
                          />
                          <button
                            type="button"
                            disabled={addCopySubmitting}
                            onClick={() => handleAddCopySubmit(book.id)}
                            className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
                          >
                            {addCopySubmitting ? "..." : "Confirmar"}
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setAddCopyBookId(null);
                              setAddCopyFormat("physical");
                            }}
                            className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
                          >
                            Cancelar
                          </button>
                        </div>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => handleToggleCopies(book.id)}
                            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            {expandedBookId === book.id ? "Ocultar copias" : "Ver copias"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setAddCopyBookId(book.id)}
                            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            Agregar copia
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Copies Section */}
                  {expandedBookId === book.id && (
                    <div className="mt-4 border-t border-gray-100 pt-4">
                      {loadingCopies === book.id && (
                        <p className="text-sm text-gray-400">Cargando copias...</p>
                      )}

                      {loadingCopies !== book.id && bookCopies[book.id]?.length === 0 && (
                        <p className="text-sm text-gray-500">
                          No tienes copias de este libro.
                        </p>
                      )}

                      {loadingCopies !== book.id && bookCopies[book.id]?.length > 0 && (
                        <div className="space-y-3">
                          {bookCopies[book.id].map((copy) => (
                            <div
                              key={copy.id}
                              className="flex items-center justify-between rounded-md bg-gray-50 px-3 py-2"
                            >
                              <div className="flex items-center gap-3">
                                <span className="text-xs font-medium text-gray-600 uppercase">
                                  {copy.format === "physical" ? "Física" : "Digital"}
                                </span>
                                {copy.format === "physical" && (
                                  <CopyStatusBadge
                                    status={copy.loan_status}
                                    borrowerName={copy.active_loan?.borrower_name}
                                    loanDate={copy.active_loan?.loan_date}
                                  />
                                )}
                              </div>

                              <div>
                                {copy.format === "physical" &&
                                  copy.loan_status === "available" &&
                                  lendCopyId !== copy.id && (
                                    <button
                                      type="button"
                                      onClick={() => handleLendClick(copy.id)}
                                      disabled={loadingLendData}
                                      className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                    >
                                      Prestar
                                    </button>
                                  )}
                              </div>
                            </div>
                          ))}

                          {/* Loan Form — shown inline below the copy list */}
                          {lendCopyId &&
                            bookCopies[book.id]?.some((c) => c.id === lendCopyId) && (
                              <div className="mt-3 rounded-md border border-blue-200 bg-blue-50 p-4">
                                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                                  Registrar préstamo
                                </h3>
                                {loadingLendData ? (
                                  <p className="text-sm text-gray-500">
                                    Cargando miembros del grupo...
                                  </p>
                                ) : groupMembers.length === 0 ? (
                                  <div>
                                    <p className="text-sm text-gray-500 mb-2">
                                      No tienes miembros en tu grupo para prestar.
                                    </p>
                                    <button
                                      type="button"
                                      onClick={handleLoanCancel}
                                      className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                                    >
                                      Cancelar
                                    </button>
                                  </div>
                                ) : (
                                  <LoanForm
                                    copyId={lendCopyId}
                                    groupMembers={groupMembers}
                                    onSuccess={handleLoanSuccess}
                                    onCancel={handleLoanCancel}
                                  />
                                )}
                              </div>
                            )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* Load More */}
              {hasMore && (
                <div className="pt-4 text-center">
                  <button
                    type="button"
                    onClick={handleLoadMore}
                    className="rounded-lg border border-gray-300 bg-white px-6 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Cargar más
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
