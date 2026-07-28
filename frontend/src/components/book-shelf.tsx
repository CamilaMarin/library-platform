"use client";

import React, { useRef, useState } from "react";
import { BookSpine } from "@/components/book-spine";
import type { Book, ReadingStatusValue } from "@/types";

interface BookShelfProps {
  /** Section label, e.g. "Leyendo ahora" */
  label: string;
  books: Book[];
  /** Map of book_id → status for all books in this shelf */
  statusMap: Record<string, ReadingStatusValue>;
  /** The status all books on this shelf share (null = unclassified shelf) */
  shelfStatus: ReadingStatusValue | null;
  /** Called when a book spine is clicked */
  onBookClick?: (book: Book) => void;
}

export function BookShelf({
  label,
  books,
  statusMap,
  shelfStatus,
  onBookClick,
}: BookShelfProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);

  // Mouse-drag horizontal scroll for desktop
  const onMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setStartX(e.pageX - (scrollRef.current?.offsetLeft ?? 0));
    setScrollLeft(scrollRef.current?.scrollLeft ?? 0);
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !scrollRef.current) return;
    e.preventDefault();
    const x = e.pageX - scrollRef.current.offsetLeft;
    scrollRef.current.scrollLeft = scrollLeft - (x - startX);
  };
  const stopDrag = () => setIsDragging(false);

  if (books.length === 0) return null;

  return (
    <section className="mb-6" aria-label={`Estante: ${label}`}>
      {/* Shelf label */}
      <h2
        className="text-sm font-semibold mb-3 tracking-wide uppercase"
        style={{ color: "var(--color-ink-faint)", letterSpacing: "0.08em" }}
      >
        {label}
        <span
          className="ml-2 text-xs font-normal normal-case"
          style={{ color: "var(--color-ink-faint)", opacity: 0.7 }}
        >
          {books.length} {books.length === 1 ? "libro" : "libros"}
        </span>
      </h2>

      {/* Shelf board */}
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
        {/* Spines row — horizontally scrollable */}
        <div
          ref={scrollRef}
          className="flex gap-2 overflow-x-auto pb-0 select-none"
          style={{
            cursor: isDragging ? "grabbing" : "grab",
            scrollbarWidth: "none", // hide scrollbar — drag to scroll
            msOverflowStyle: "none",
          }}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={stopDrag}
          onMouseLeave={stopDrag}
        >
          {books.map((book) => (
            <BookSpine
              key={book.id}
              book={book}
              status={statusMap[book.id] ?? shelfStatus}
              onBookClick={onBookClick}
              height={120}
            />
          ))}
          {/* Right padding spacer */}
          <div style={{ minWidth: 8, flexShrink: 0 }} aria-hidden="true" />
        </div>

        {/* Shelf table — teak horizontal line */}
        <div
          aria-hidden="true"
          style={{
            height: 6,
            background:
              "linear-gradient(to bottom, var(--color-teak), var(--color-mahogany))",
            borderRadius: "0 0 6px 6px",
            marginTop: 2,
            boxShadow: "0 2px 6px rgba(28,16,8,0.18)",
          }}
        />
      </div>
    </section>
  );
}
