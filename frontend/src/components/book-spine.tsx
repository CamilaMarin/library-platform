"use client";

import React, { useState } from "react";
import type { Book, ReadingStatusValue } from "@/types";

// ── Palette: one background per status ──────────────────────────────────────
const SPINE_COLORS: Record<string, string> = {
  reading:      "var(--color-reading)",   // dark green
  read:         "var(--color-walnut)",    // very dark brown
  want_to_read: "var(--color-teak)",      // medium brown
  dnf:          "var(--color-mahogany)",  // reddish brown
  none:         "var(--color-aged)",      // light parchment — unclassified
};

const SPINE_TEXT_COLORS: Record<string, string> = {
  reading:      "var(--color-cream)",
  read:         "var(--color-parchment)",
  want_to_read: "var(--color-cream)",
  dnf:          "var(--color-parchment)",
  none:         "var(--color-ink-soft)",
};

interface BookSpineProps {
  book: Book;
  status: ReadingStatusValue | null;
  /** Called when user clicks the spine to see book details. */
  onBookClick?: (book: Book) => void;
  /** Height of the spine in px. Defaults to 120. */
  height?: number;
}

export function BookSpine({
  book,
  status,
  onBookClick,
  height = 120,
}: BookSpineProps) {
  const colorKey = status ?? "none";
  const bg = SPINE_COLORS[colorKey];
  const textColor = SPINE_TEXT_COLORS[colorKey];

  const [hovered, setHovered] = useState(false);

  return (
    <button
      type="button"
      aria-label={`${book.title} por ${book.author}. Clic para ver detalle.`}
      onClick={() => onBookClick?.(book)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="relative flex-shrink-0 flex flex-col justify-end items-center focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1"
      style={{
        width: 36,
        height,
        background: bg,
        borderRadius: "2px 5px 5px 2px",
        boxShadow: hovered
          ? "3px 0 10px rgba(28,16,8,0.40), inset -1px 0 0 rgba(255,255,255,0.10)"
          : "2px 0 6px rgba(28,16,8,0.28), inset -1px 0 0 rgba(255,255,255,0.07)",
        transform: hovered ? "translateY(-4px)" : "translateY(0)",
        transition: "transform 0.15s ease, box-shadow 0.15s ease",
        cursor: "pointer",
        overflow: "hidden",
        padding: 0,
        border: "none",
      }}
    >
      {/* Title — rotated */}
      <span
        className="absolute inset-0 flex items-center justify-center"
        style={{
          writingMode: "vertical-rl",
          transform: "rotate(180deg)",
          fontSize: 10,
          fontFamily: "var(--font-playfair), Georgia, serif",
          color: textColor,
          fontStyle: "italic",
          letterSpacing: "0.03em",
          padding: "6px 4px",
          lineHeight: 1.2,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          maxHeight: "100%",
          pointerEvents: "none",
        }}
        aria-hidden="true"
      >
        {book.title}
      </span>

      {/* Brass bottom accent */}
      <span
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 4,
          background: "var(--color-brass)",
          opacity: 0.7,
          borderRadius: "0 0 5px 0",
          pointerEvents: "none",
        }}
        aria-hidden="true"
      />
    </button>
  );
}
