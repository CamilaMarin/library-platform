"use client";

import { useEffect, useState, useCallback } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { LoanCard } from "@/components/loan-card";
import { BookSpine } from "@/components/book-spine";
import { BookDetailModal } from "@/components/book-detail-modal";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPatch, apiPut, apiDelete, ApiError } from "@/lib/api-client";
import type { LoanWithDetails, Book, ReadingStatusValue } from "@/types";

type TabStatus = "active" | "returned" | "borrowed";

const TABS: { id: TabStatus; label: string }[] = [
  { id: "active",   label: "Activos" },
  { id: "returned", label: "Historial" },
  { id: "borrowed", label: "Me prestaron" },
];

export default function LoansPage() {
  const [activeTab, setActiveTab] = useState<TabStatus>("active");
  const [loans, setLoans] = useState<LoanWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [returningLoanId, setReturningLoanId] = useState<string | null>(null);
  const { showToast } = useToast();

  // Borrowed books shelf state
  const [borrowedBooks, setBorrowedBooks] = useState<Book[]>([]);
  const [borrowedStatusMap, setBorrowedStatusMap] = useState<Record<string, ReadingStatusValue>>({});
  const [detailBook, setDetailBook] = useState<Book | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailStatus, setDetailStatus] = useState<{ status: string; current_page: number | null } | null>(null);

  const fetchLoans = useCallback(async (tab: TabStatus) => {
    setLoading(true);
    try {
      let data: LoanWithDetails[];
      if (tab === "borrowed") {
        data = await apiGet<LoanWithDetails[]>("/loans/borrowed");

        // Build Book objects from loan data for the shelf
        const books: Book[] = data
          .filter((loan) => loan.book_id)
          .map((loan) => ({
            id: loan.book_id!,
            title: loan.book_title,
            author: loan.borrower_name, // In borrowed context, borrower_name holds lender name
            genres: [],
            description: null,
            pages: null,
            isbn: null,
            created_at: "",
          }));
        setBorrowedBooks(books);

        // Fetch reading statuses for these books
        try {
          const statuses = await apiGet<{ book_id: string; status: ReadingStatusValue; current_page: number | null }[]>("/books/statuses");
          const map: Record<string, ReadingStatusValue> = {};
          for (const s of statuses) {
            map[s.book_id] = s.status;
          }
          setBorrowedStatusMap(map);
        } catch {
          setBorrowedStatusMap({});
        }
      } else {
        data = await apiGet<LoanWithDetails[]>(`/loans?status=${tab}`);
        setBorrowedBooks([]);
      }
      setLoans(data);
    } catch {
      setLoans([]);
      setBorrowedBooks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLoans(activeTab);
  }, [activeTab, fetchLoans]);

  const handleReturn = async (loanId: string) => {
    setReturningLoanId(loanId);
    try {
      await apiPatch(`/loans/${loanId}/return`);
      showToast("Préstamo devuelto", "success");
      fetchLoans(activeTab);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        showToast("Préstamo no encontrado.", "error");
      }
    } finally {
      setReturningLoanId(null);
    }
  };

  // Borrowed shelf: click a spine to open book detail
  const handleBorrowedBookClick = useCallback(async (book: Book) => {
    setDetailBook(book);
    setDetailOpen(true);

    // Fetch full book details (for pages, genres, description, etc.)
    try {
      const fullBook = await apiGet<Book>(`/books/${book.id}`);
      setDetailBook(fullBook);
    } catch {
      // Keep the partial book data if fetch fails
    }

    // Get this book's reading status
    try {
      const statuses = await apiGet<{ book_id: string; status: string; current_page: number | null }[]>("/books/statuses");
      const match = statuses.find((s) => s.book_id === book.id);
      setDetailStatus(match || null);
    } catch {
      setDetailStatus(null);
    }
  }, []);

  const handleBorrowedStatusChange = useCallback(async (bookId: string, status: ReadingStatusValue | null) => {
    try {
      if (status) {
        await apiPut(`/books/${bookId}/status`, { status });
        setBorrowedStatusMap((prev) => ({ ...prev, [bookId]: status }));
        setDetailStatus((prev) => prev ? { ...prev, status } : { status, current_page: null });
      } else {
        await apiDelete(`/books/${bookId}/status`);
        setBorrowedStatusMap((prev) => {
          const next = { ...prev };
          delete next[bookId];
          return next;
        });
        setDetailStatus(null);
      }
    } catch {
      // silent
    }
  }, []);

  const handleBorrowedProgressUpdate = useCallback(() => {
    // Refresh the status for the current detail book
    if (detailBook) {
      handleBorrowedBookClick(detailBook);
    }
  }, [detailBook, handleBorrowedBookClick]);

  const handleDetailClose = useCallback(() => {
    setDetailOpen(false);
    setDetailBook(null);
    setDetailStatus(null);
  }, []);

  return (
    <ProtectedRoute>
      <Navigation />
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <h1
            className="text-2xl font-bold mb-6"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--color-walnut)",
            }}
          >
            Mis Préstamos
          </h1>

          {/* Tabs */}
          <div
            className="flex gap-1 mb-6 p-1 rounded-lg w-fit"
            style={{ background: "var(--color-aged)" }}
          >
            {TABS.map((tab) => {
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
                  style={
                    active
                      ? {
                          background: "var(--color-cream)",
                          color: "var(--color-walnut)",
                          boxShadow: "0 1px 3px rgba(28,16,8,0.12)",
                        }
                      : {
                          background: "transparent",
                          color: "var(--color-ink-soft)",
                        }
                  }
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Content */}
          {loading ? (
            <Skeleton variant="card" count={3} />
          ) : loans.length === 0 ? (
            <div
              className="rounded-lg p-8 text-center"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
              }}
            >
              <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                {activeTab === "active"
                  ? "No tienes préstamos activos."
                  : activeTab === "returned"
                  ? "No tienes préstamos devueltos."
                  : "No te han prestado libros."}
              </p>
            </div>
          ) : activeTab === "borrowed" ? (
            /* Shelf view for borrowed books */
            <div>
              {/* Active borrowed shelf */}
              {(() => {
                const activeLoans = loans.filter((l) => l.status === "active");
                const activeBooks = activeLoans
                  .filter((l) => l.book_id)
                  .map((l) => borrowedBooks.find((b) => b.id === l.book_id))
                  .filter(Boolean) as Book[];

                if (activeBooks.length > 0) {
                  return (
                    <section className="mb-6">
                      <h2
                        className="text-sm font-semibold mb-3 tracking-wide uppercase"
                        style={{ color: "var(--color-ink-faint)", letterSpacing: "0.08em" }}
                      >
                        Prestados activos
                        <span className="ml-2 text-xs font-normal normal-case" style={{ opacity: 0.7 }}>
                          {activeBooks.length} {activeBooks.length === 1 ? "libro" : "libros"}
                        </span>
                      </h2>
                      <div
                        className="relative"
                        style={{
                          background: "var(--color-cream)",
                          border: "1px solid var(--color-border)",
                          borderRadius: 8,
                          padding: "16px 16px 0 16px",
                          boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                        }}
                      >
                        <div className="flex gap-2 overflow-x-auto pb-0" style={{ scrollbarWidth: "none" }}>
                          {activeBooks.map((book) => (
                            <BookSpine
                              key={book.id}
                              book={book}
                              status={borrowedStatusMap[book.id] ?? null}
                              onBookClick={handleBorrowedBookClick}
                              height={120}
                            />
                          ))}
                          <div style={{ minWidth: 8, flexShrink: 0 }} aria-hidden="true" />
                        </div>
                        <div
                          aria-hidden="true"
                          style={{
                            height: 6,
                            background: "linear-gradient(to bottom, var(--color-teak), var(--color-mahogany))",
                            borderRadius: "0 0 6px 6px",
                            marginTop: 2,
                            boxShadow: "0 2px 6px rgba(28,16,8,0.18)",
                          }}
                        />
                      </div>
                    </section>
                  );
                }
                return null;
              })()}

              {/* Returned borrowed shelf */}
              {(() => {
                const returnedLoans = loans.filter((l) => l.status === "returned");
                const returnedBooks = returnedLoans
                  .filter((l) => l.book_id)
                  .map((l) => borrowedBooks.find((b) => b.id === l.book_id))
                  .filter(Boolean) as Book[];

                if (returnedBooks.length > 0) {
                  return (
                    <section className="mb-6">
                      <h2
                        className="text-sm font-semibold mb-3 tracking-wide uppercase"
                        style={{ color: "var(--color-ink-faint)", letterSpacing: "0.08em" }}
                      >
                        Devueltos
                        <span className="ml-2 text-xs font-normal normal-case" style={{ opacity: 0.7 }}>
                          {returnedBooks.length} {returnedBooks.length === 1 ? "libro" : "libros"}
                        </span>
                      </h2>
                      <div
                        className="relative"
                        style={{
                          background: "var(--color-cream)",
                          border: "1px solid var(--color-border)",
                          borderRadius: 8,
                          padding: "16px 16px 0 16px",
                          boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                          opacity: 0.75,
                        }}
                      >
                        <div className="flex gap-2 overflow-x-auto pb-0" style={{ scrollbarWidth: "none" }}>
                          {returnedBooks.map((book) => (
                            <BookSpine
                              key={book.id}
                              book={book}
                              status={borrowedStatusMap[book.id] ?? null}
                              onBookClick={handleBorrowedBookClick}
                              height={100}
                            />
                          ))}
                          <div style={{ minWidth: 8, flexShrink: 0 }} aria-hidden="true" />
                        </div>
                        <div
                          aria-hidden="true"
                          style={{
                            height: 6,
                            background: "linear-gradient(to bottom, var(--color-teak), var(--color-mahogany))",
                            borderRadius: "0 0 6px 6px",
                            marginTop: 2,
                            boxShadow: "0 2px 6px rgba(28,16,8,0.18)",
                          }}
                        />
                      </div>
                    </section>
                  );
                }
                return null;
              })()}

              {/* Loan detail cards below */}
              <div className="space-y-3 mt-4">
                {loans.map((loan) => (
                  <LoanCard
                    key={loan.id}
                    loan={loan}
                    variant={loan.status === "returned" ? "returned" : "active"}
                    isBorrowedView={true}
                  />
                ))}
              </div>
            </div>
          ) : (
            /* Standard card view for active/returned */
            <div className="flex flex-col gap-4">
              {loans.map((loan) => (
                <LoanCard
                  key={loan.id}
                  loan={loan}
                  variant={activeTab}
                  onReturn={activeTab === "active" ? handleReturn : undefined}
                  isReturning={returningLoanId === loan.id}
                />
              ))}
            </div>
          )}
        </div>

        {/* Book Detail Modal for borrowed books */}
        <BookDetailModal
          book={detailBook}
          copies={[]}
          open={detailOpen}
          loadingCopies={false}
          onClose={handleDetailClose}
          readingStatus={detailStatus}
          onProgressUpdate={handleBorrowedProgressUpdate}
          onStatusChange={handleBorrowedStatusChange}
        />
      </main>
    </ProtectedRoute>
  );
}
