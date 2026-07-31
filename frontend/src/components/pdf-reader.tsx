"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { ChevronLeft, ChevronRight, X, Loader2 } from "lucide-react";
import { getAccessToken } from "@/lib/token-storage";
import { useReadingProgress } from "@/lib/use-reading-progress";

import * as pdfjsLib from "pdfjs-dist";

// Configure PDF.js worker from CDN
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.9.155/pdf.worker.min.mjs`;

interface PdfReaderProps {
  copyId: string;
  fileUrl: string;
  onClose: () => void;
}

export function PdfReader({ copyId, fileUrl, onClose }: PdfReaderProps) {
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [pageInputValue, setPageInputValue] = useState("1");
  const [pdfLoading, setPdfLoading] = useState(true);
  const [renderingPage, setRenderingPage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const renderTaskRef = useRef<pdfjsLib.RenderTask | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { currentProgress, saveProgress, loading: progressLoading } =
    useReadingProgress(copyId);

  // Load the PDF document
  useEffect(() => {
    let cancelled = false;

    async function loadPdf() {
      try {
        setPdfLoading(true);
        setError(null);

        const token = getAccessToken();
        const response = await fetch(fileUrl, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        if (!response.ok) {
          if (response.status === 403) {
            throw new Error("No tienes permiso para acceder a este archivo.");
          }
          throw new Error(`Error al cargar el archivo (${response.status}).`);
        }

        const arrayBuffer = await response.arrayBuffer();
        const doc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

        if (!cancelled) {
          setPdfDoc(doc);
          setTotalPages(doc.numPages);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Error al cargar el PDF."
          );
        }
      } finally {
        if (!cancelled) {
          setPdfLoading(false);
        }
      }
    }

    loadPdf();

    return () => {
      cancelled = true;
    };
  }, [fileUrl]);

  // Restore last reading position once both PDF and progress are loaded
  useEffect(() => {
    if (pdfDoc && !progressLoading && currentProgress) {
      const savedPage = parseInt(currentProgress.position, 10);
      if (!isNaN(savedPage) && savedPage >= 1 && savedPage <= pdfDoc.numPages) {
        setCurrentPage(savedPage);
        setPageInputValue(String(savedPage));
      }
    }
  }, [pdfDoc, progressLoading, currentProgress]);

  // Render the current page
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    let cancelled = false;

    async function renderPage() {
      if (!pdfDoc || !canvasRef.current) return;

      // Cancel any in-progress render
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
        renderTaskRef.current = null;
      }

      setRenderingPage(true);

      try {
        const page = await pdfDoc.getPage(currentPage);

        if (cancelled) return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const context = canvas.getContext("2d");
        if (!context) return;

        // Calculate scale to fit container width (mobile-responsive)
        const containerWidth = containerRef.current?.clientWidth ?? 800;
        const maxWidth = Math.min(containerWidth - 32, 900); // 16px padding each side
        const viewport = page.getViewport({ scale: 1 });
        const scale = maxWidth / viewport.width;
        const scaledViewport = page.getViewport({ scale });

        canvas.height = scaledViewport.height;
        canvas.width = scaledViewport.width;

        const renderTask = page.render({
          canvasContext: context,
          viewport: scaledViewport,
        });

        renderTaskRef.current = renderTask;
        await renderTask.promise;

        if (!cancelled) {
          setRenderingPage(false);
        }
      } catch (err) {
        if (!cancelled && (err as Error).name !== "RenderingCancelledException") {
          setRenderingPage(false);
          console.error("Error rendering page:", err);
        }
      }
    }

    renderPage();

    return () => {
      cancelled = true;
    };
  }, [pdfDoc, currentPage]);

  // Navigate and save progress
  const goToPage = useCallback(
    (page: number) => {
      if (page < 1 || page > totalPages) return;
      setCurrentPage(page);
      setPageInputValue(String(page));
      saveProgress(String(page), page / totalPages, "pdf");
    },
    [totalPages, saveProgress]
  );

  const goToPrev = useCallback(() => {
    goToPage(currentPage - 1);
  }, [currentPage, goToPage]);

  const goToNext = useCallback(() => {
    goToPage(currentPage + 1);
  }, [currentPage, goToPage]);

  // Handle page input submission
  const handlePageInputSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const page = parseInt(pageInputValue, 10);
      if (!isNaN(page) && page >= 1 && page <= totalPages) {
        goToPage(page);
      } else {
        setPageInputValue(String(currentPage));
      }
    },
    [pageInputValue, totalPages, currentPage, goToPage]
  );

  // Keyboard navigation
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        goToPrev();
      } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        goToNext();
      } else if (e.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goToPrev, goToNext, onClose]);

  // Loading state
  if (pdfLoading || progressLoading) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ backgroundColor: "var(--color-walnut)" }}
      >
        <div className="flex flex-col items-center gap-4">
          <Loader2
            className="h-10 w-10 animate-spin"
            style={{ color: "var(--color-cream)" }}
          />
          <p
            className="text-sm"
            style={{ color: "var(--color-aged)" }}
          >
            Cargando documento...
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ backgroundColor: "var(--color-walnut)" }}
      >
        <div className="flex flex-col items-center gap-4 px-6 text-center">
          <p
            className="text-lg font-medium"
            style={{ color: "var(--color-cream)" }}
          >
            {error}
          </p>
          <button
            onClick={onClose}
            className="btn-primary mt-4"
          >
            Cerrar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col"
      style={{ backgroundColor: "var(--color-walnut)" }}
    >
      {/* Header toolbar */}
      <header
        className="flex items-center justify-between px-4 py-3 shrink-0"
        style={{
          backgroundColor: "var(--color-mahogany)",
          borderBottom: "1px solid var(--color-teak)",
        }}
      >
        {/* Page navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={goToPrev}
            disabled={currentPage <= 1}
            className="rounded-full p-2 transition-colors disabled:opacity-30"
            style={{ color: "var(--color-cream)" }}
            aria-label="Página anterior"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>

          <form
            onSubmit={handlePageInputSubmit}
            className="flex items-center gap-1"
          >
            <input
              type="text"
              inputMode="numeric"
              value={pageInputValue}
              onChange={(e) => setPageInputValue(e.target.value)}
              onBlur={handlePageInputSubmit}
              className="w-12 rounded px-2 py-1 text-center text-sm"
              style={{
                backgroundColor: "var(--color-walnut)",
                color: "var(--color-cream)",
                border: "1px solid var(--color-teak)",
              }}
              aria-label="Número de página"
            />
            <span
              className="text-sm"
              style={{ color: "var(--color-aged)" }}
            >
              / {totalPages}
            </span>
          </form>

          <button
            onClick={goToNext}
            disabled={currentPage >= totalPages}
            className="rounded-full p-2 transition-colors disabled:opacity-30"
            style={{ color: "var(--color-cream)" }}
            aria-label="Página siguiente"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="rounded-full p-2 transition-colors"
          style={{ color: "var(--color-cream)" }}
          aria-label="Cerrar lector"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      {/* PDF canvas area */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto flex items-start justify-center py-4"
      >
        <div className="relative">
          {renderingPage && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2
                className="h-6 w-6 animate-spin"
                style={{ color: "var(--color-cream)" }}
              />
            </div>
          )}
          <canvas
            ref={canvasRef}
            className="block max-w-full"
            style={{ opacity: renderingPage ? 0.5 : 1 }}
          />
        </div>
      </div>

      {/* Bottom navigation for mobile (touch-friendly) */}
      <footer
        className="flex items-center justify-between px-6 py-3 shrink-0 sm:hidden"
        style={{
          backgroundColor: "var(--color-mahogany)",
          borderTop: "1px solid var(--color-teak)",
        }}
      >
        <button
          onClick={goToPrev}
          disabled={currentPage <= 1}
          className="rounded-full px-4 py-2 text-sm font-medium disabled:opacity-30"
          style={{
            backgroundColor: "var(--color-walnut)",
            color: "var(--color-cream)",
          }}
        >
          Anterior
        </button>
        <span
          className="text-sm"
          style={{ color: "var(--color-aged)" }}
        >
          {currentPage} / {totalPages}
        </span>
        <button
          onClick={goToNext}
          disabled={currentPage >= totalPages}
          className="rounded-full px-4 py-2 text-sm font-medium disabled:opacity-30"
          style={{
            backgroundColor: "var(--color-walnut)",
            color: "var(--color-cream)",
          }}
        >
          Siguiente
        </button>
      </footer>
    </div>
  );
}
