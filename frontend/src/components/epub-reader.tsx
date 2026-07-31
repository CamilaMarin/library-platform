"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { X, ChevronLeft, ChevronRight, Loader2, BookOpen } from "lucide-react";
import { getAccessToken } from "@/lib/token-storage";
import { useReadingProgress } from "@/lib/use-reading-progress";
import type Book from "epubjs/types/book";
import type Rendition from "epubjs/types/rendition";
import type { Location } from "epubjs/types/rendition";

interface EpubReaderProps {
  copyId: string;
  fileUrl: string;
  onClose: () => void;
}

/**
 * EpubReader — renders an EPUB file using epub.js with CFI-based progress tracking.
 *
 * ⚠️ HIGH RISK (MVP): epub.js CFI positioning is complex and may not work perfectly
 * with all EPUB files. Accept imperfect pagination for MVP.
 */
export function EpubReader({ copyId, fileUrl, onClose }: EpubReaderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bookRef = useRef<Book | null>(null);
  const renditionRef = useRef<Rendition | null>(null);

  const [epubLoading, setEpubLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chapterTitle, setChapterTitle] = useState<string>("");
  const [percentage, setPercentage] = useState<number>(0);

  const { currentProgress, saveProgress, loading: progressLoading } =
    useReadingProgress(copyId);

  const locationsGeneratedRef = useRef(false);
  const initialDisplayDoneRef = useRef(false);

  // Load EPUB and render
  useEffect(() => {
    let destroyed = false;

    async function loadEpub() {
      try {
        // Fetch the binary EPUB file with auth
        const token = getAccessToken();
        const response = await fetch(fileUrl, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        if (!response.ok) {
          setError(
            response.status === 403
              ? "No tienes permiso para acceder a este archivo."
              : "Error al cargar el archivo EPUB."
          );
          setEpubLoading(false);
          return;
        }

        const arrayBuffer = await response.arrayBuffer();

        if (destroyed) return;

        // Dynamically import epub.js (client-side only)
        const ePub = (await import("epubjs")).default;
        const book = ePub(arrayBuffer);
        bookRef.current = book;

        await book.ready;
        if (destroyed) return;

        if (!containerRef.current) return;

        const rendition = book.renderTo(containerRef.current, {
          width: "100%",
          height: "100%",
          flow: "paginated",
          allowScriptedContent: false,
        });
        renditionRef.current = rendition;

        // Generate locations for percentage calculation
        book.locations.generate(1024).then(() => {
          locationsGeneratedRef.current = true;
        });

        // Display initial position (restored or start)
        if (currentProgress?.position && currentProgress.file_format === "epub") {
          await rendition.display(currentProgress.position);
        } else {
          await rendition.display();
        }

        initialDisplayDoneRef.current = true;

        if (!destroyed) {
          setEpubLoading(false);
        }
      } catch {
        if (!destroyed) {
          setError("Error al cargar el archivo EPUB.");
          setEpubLoading(false);
        }
      }
    }

    // Wait for progress to load before initializing (so we can restore position)
    if (!progressLoading) {
      loadEpub();
    }

    return () => {
      destroyed = true;
      if (renditionRef.current) {
        renditionRef.current.destroy();
        renditionRef.current = null;
      }
      if (bookRef.current) {
        bookRef.current.destroy();
        bookRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progressLoading]);

  // Listen to relocation events for progress tracking
  useEffect(() => {
    const rendition = renditionRef.current;
    const book = bookRef.current;
    if (!rendition || !book || epubLoading) return;

    const handleRelocated = (location: Location) => {
      if (!initialDisplayDoneRef.current) return;

      const cfi = location.start.cfi;

      // Calculate percentage
      let pct = 0;
      if (locationsGeneratedRef.current) {
        pct = book.locations.percentageFromCfi(cfi);
      } else if (location.start.percentage !== undefined) {
        pct = location.start.percentage;
      }
      setPercentage(pct);

      // Save progress with CFI position
      saveProgress(cfi, pct, "epub");

      // Update chapter title from navigation
      if (book.navigation) {
        const navItem = book.navigation.toc.find((item) => {
          // Match by href (approximate — TOC structure varies by EPUB)
          return location.start.href?.includes(item.href?.split("#")[0] ?? "");
        });
        if (navItem) {
          setChapterTitle(navItem.label?.trim() ?? "");
        }
      }
    };

    rendition.on("relocated", handleRelocated);

    return () => {
      rendition.off("relocated", handleRelocated);
    };
  }, [epubLoading, saveProgress]);

  const goNext = useCallback(() => {
    renditionRef.current?.next();
  }, []);

  const goPrev = useCallback(() => {
    renditionRef.current?.prev();
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") {
        goNext();
      } else if (e.key === "ArrowLeft") {
        goPrev();
      } else if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goNext, goPrev, onClose]);

  if (error) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ backgroundColor: "var(--color-parchment)" }}
      >
        <div className="text-center p-8">
          <p className="text-lg mb-4" style={{ color: "var(--color-ink)" }}>
            {error}
          </p>
          <button onClick={onClose} className="btn-primary">
            Cerrar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col"
      style={{ backgroundColor: "var(--color-cream)" }}
    >
      {/* Top bar */}
      <header
        className="flex items-center justify-between px-4 py-2 shrink-0"
        style={{
          backgroundColor: "var(--color-walnut)",
          color: "var(--color-cream)",
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <BookOpen className="w-4 h-4 shrink-0" />
          <span className="text-sm truncate">{chapterTitle || "EPUB"}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs opacity-75">
            {Math.round(percentage * 100)}%
          </span>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-white/10 transition-colors"
            aria-label="Cerrar lector"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Reader content area */}
      <div className="flex-1 relative overflow-hidden">
        {(epubLoading || progressLoading) && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <div className="flex flex-col items-center gap-3">
              <Loader2
                className="w-8 h-8 animate-spin"
                style={{ color: "var(--color-teak)" }}
              />
              <span
                className="text-sm"
                style={{ color: "var(--color-ink-soft)" }}
              >
                Cargando libro...
              </span>
            </div>
          </div>
        )}

        <div
          ref={containerRef}
          className="w-full h-full"
          style={{
            opacity: epubLoading ? 0 : 1,
            transition: "opacity 0.3s ease",
          }}
        />

        {/* Navigation buttons — overlaid on sides */}
        {!epubLoading && (
          <>
            <button
              onClick={goPrev}
              className="absolute left-0 top-0 bottom-0 w-12 md:w-16 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
              style={{ backgroundColor: "rgba(44, 31, 20, 0.05)" }}
              aria-label="Página anterior"
            >
              <ChevronLeft
                className="w-6 h-6"
                style={{ color: "var(--color-walnut)" }}
              />
            </button>
            <button
              onClick={goNext}
              className="absolute right-0 top-0 bottom-0 w-12 md:w-16 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
              style={{ backgroundColor: "rgba(44, 31, 20, 0.05)" }}
              aria-label="Página siguiente"
            >
              <ChevronRight
                className="w-6 h-6"
                style={{ color: "var(--color-walnut)" }}
              />
            </button>
          </>
        )}
      </div>

      {/* Bottom progress bar */}
      <div
        className="h-1 shrink-0"
        style={{ backgroundColor: "var(--color-aged)" }}
      >
        <div
          className="h-full transition-all duration-300"
          style={{
            width: `${Math.round(percentage * 100)}%`,
            backgroundColor: "var(--color-reading)",
          }}
        />
      </div>
    </div>
  );
}
