"use client";

import React from "react";
import { LoanWithDetails } from "@/types";

interface LoanCardProps {
  loan: LoanWithDetails;
  variant: "active" | "returned";
  onReturn?: (loanId: string) => Promise<void>;
  isReturning?: boolean;
  isBorrowedView?: boolean;
}

function formatDate(dateStr: string): string {
  // Parse the date treating it as a local date to avoid timezone offset issues.
  // If the string contains "T00:00:00" (date-only stored as midnight UTC),
  // extract just the date part to prevent timezone shift.
  let date: Date;
  if (dateStr.includes("T00:00:00") || dateStr.length === 10) {
    const parts = dateStr.split("T")[0].split("-");
    date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
  } else {
    date = new Date(dateStr);
  }
  return date.toLocaleDateString("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function LoanCard({
  loan,
  variant,
  onReturn,
  isReturning = false,
  isBorrowedView = false,
}: LoanCardProps) {
  return (
    <article
      className="rounded-lg p-4"
      style={{
        background: "var(--color-cream)",
        border: "1px solid var(--color-border)",
        boxShadow: "0 1px 3px rgba(28, 16, 8, 0.08)",
      }}
      aria-label={`Préstamo: ${loan.book_title}`}
    >
      <h3
        className="text-base font-semibold"
        style={{
          fontFamily: "var(--font-playfair), Georgia, serif",
          color: "var(--color-walnut)",
        }}
      >
        {loan.book_title}
      </h3>
      <p className="mt-1 text-sm" style={{ color: "var(--color-ink-soft)" }}>
        {isBorrowedView ? "Prestado por:" : "Prestado a:"}{" "}
        <span style={{ color: "var(--color-ink)" }}>{loan.borrower_name}</span>
      </p>
      <p className="mt-1 text-sm" style={{ color: "var(--color-ink-faint)" }}>
        Fecha de préstamo:{" "}
        <span style={{ color: "var(--color-ink-soft)" }}>
          {formatDate(loan.loan_date)}
        </span>
      </p>

      {variant === "active" && loan.estimated_return_date && (
        <p className="mt-1 text-sm" style={{ color: "var(--color-ink-faint)" }}>
          Devolución estimada:{" "}
          <span style={{ color: "var(--color-ink-soft)" }}>
            {formatDate(loan.estimated_return_date)}
          </span>
        </p>
      )}

      {variant === "returned" && loan.returned_date && (
        <p className="mt-1 text-sm" style={{ color: "var(--color-ink-faint)" }}>
          Devuelto el:{" "}
          <span style={{ color: "var(--color-ink-soft)" }}>
            {formatDate(loan.returned_date)}
          </span>
        </p>
      )}

      {variant === "active" && onReturn && (
        <button
          type="button"
          onClick={() => onReturn(loan.id)}
          disabled={isReturning}
          className="mt-3 rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: "var(--color-walnut)",
            color: "var(--color-cream)",
          }}
          onMouseEnter={(e) => {
            if (!isReturning)
              (e.currentTarget as HTMLButtonElement).style.background =
                "var(--color-mahogany)";
          }}
          onMouseLeave={(e) => {
            if (!isReturning)
              (e.currentTarget as HTMLButtonElement).style.background =
                "var(--color-walnut)";
          }}
        >
          {isReturning ? "Devolviendo..." : "Marcar devuelto"}
        </button>
      )}
    </article>
  );
}
