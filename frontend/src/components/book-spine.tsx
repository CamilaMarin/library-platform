"use client";

import React, { useRef, useEffect, useState } from "react";
import type { Book, ReadingStatusValue } from "@/types";
import { READING_STATUS_LABELS } from "@/types";

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

// Status options shown in the popover menu
const STATUS_OPTIONS: { value: ReadingStatusValue | "none"; label: string }[] = [
  { value: "reading",      label: "Leyendo ahora" },
  { value: "want_to_read", label: "Quiero leer" },
  { value: "read",         label: "Leído" },
  { value: "dnf",          label: "No terminado" },
  { value: "none",         label: "Sin clasificar" },
];

interface BookSpineProps {
  book: Book;
  status: ReadingStatusValue | null;
  /** Called when user selects a new status or removes it (null = remove). */
  onStatusChange: (bookId: string, status: ReadingStatusValue | null) => void;
  /** Height of the spine in px. Defaults to 120. */
  height?: number;
}

export function BookSpine({
  book,
  status,
  onStatusChange,
  height = 120,
}: BookSpineProps) {
  const colorKey = status ?? "none";
  const bg = SPINE_COLORS[colorKey];
  const textColor = SPINE_TEXT_COLORS[colorKey];

  const [menuOpen, setMenuOpen] = useState(false);
  const [hovered, setHovered] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [menuOpen]);

  // Close menu on Escape
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [menuOpen]);

  const handleSelect = (value: ReadingStatusValue | "none") => {
    onStatusChange(book.id, value === "none" ? null : value);
    setMenuOpen(false);
  };

  const statusLabel = status ? READING_STATUS_LABELS[status] : "Sin clasificar";

  return (
    <div
      ref={wrapperRef}
      className="relative flex-shrink-0"
      style={{ width: 36 }}
    >
      {/* ── The spine itself ──────────────────────────────────────── */}
      <button
        type="button"
        aria-label={`${book.title} — ${statusLabel}. Clic para cambiar estado.`}
        aria-haspopup="listbox"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((v) => !v)}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        className="flex flex-col justify-end items-center focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1"
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

      {/* ── Status popover menu ────────────────────────────────────── */}
      {menuOpen && (
        <div
          role="listbox"
          aria-label={`Estado de lectura para ${book.title}`}
          className="absolute z-50 bottom-full mb-2 left-1/2 -translate-x-1/2 rounded-lg py-1 min-w-[160px]"
          style={{
            background: "var(--color-cream)",
            border: "1px solid var(--color-border)",
            boxShadow: "0 8px 24px -4px rgba(28,16,8,0.20)",
          }}
        >
          {/* Book title tooltip */}
          <p
            className="px-3 py-1.5 text-[11px] font-medium border-b truncate"
            style={{
              color: "var(--color-ink-faint)",
              borderColor: "var(--color-border)",
              maxWidth: 160,
            }}
            title={book.title}
          >
            {book.title}
          </p>

          {STATUS_OPTIONS.map((opt) => {
            const isCurrent =
              opt.value === "none" ? status === null : opt.value === status;
            return (
              <button
                key={opt.value}
                role="option"
                aria-selected={isCurrent}
                type="button"
                onClick={() => handleSelect(opt.value)}
                className="w-full text-left px-3 py-1.5 text-xs transition-colors flex items-center gap-2"
                style={{
                  color: isCurrent
                    ? "var(--color-walnut)"
                    : "var(--color-ink-soft)",
                  background: isCurrent ? "var(--color-parchment)" : "transparent",
                  fontWeight: isCurrent ? 600 : 400,
                }}
                onMouseEnter={(e) => {
                  if (!isCurrent)
                    (e.currentTarget as HTMLButtonElement).style.background =
                      "var(--color-parchment)";
                }}
                onMouseLeave={(e) => {
                  if (!isCurrent)
                    (e.currentTarget as HTMLButtonElement).style.background =
                      "transparent";
                }}
              >
                {/* Color dot */}
                <span
                  aria-hidden="true"
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    flexShrink: 0,
                    background:
                      opt.value === "none"
                        ? "var(--color-aged)"
                        : SPINE_COLORS[opt.value],
                  }}
                />
                {opt.label}
                {isCurrent && (
                  <span
                    aria-hidden="true"
                    className="ml-auto"
                    style={{ color: "var(--color-brass)" }}
                  >
                    ✓
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
