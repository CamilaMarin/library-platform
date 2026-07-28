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
    // Date-only: parse as local (YYYY-MM-DD)
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
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      aria-label={`Préstamo: ${loan.book_title}`}
    >
      <h3 className="text-base font-bold text-gray-900">{loan.book_title}</h3>
      <p className="mt-1 text-sm text-gray-600">
        {isBorrowedView ? "Prestado por:" : "Prestado a:"} {loan.borrower_name}
      </p>
      <p className="mt-1 text-sm text-gray-500">
        Fecha de préstamo: {formatDate(loan.loan_date)}
      </p>

      {variant === "active" && loan.estimated_return_date && (
        <p className="mt-1 text-sm text-gray-500">
          Devolución estimada: {formatDate(loan.estimated_return_date)}
        </p>
      )}

      {variant === "returned" && loan.returned_date && (
        <p className="mt-1 text-sm text-gray-500">
          Devuelto el: {formatDate(loan.returned_date)}
        </p>
      )}

      {variant === "active" && onReturn && (
        <button
          type="button"
          onClick={() => onReturn(loan.id)}
          disabled={isReturning}
          className="mt-3 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isReturning ? "Devolviendo..." : "Marcar devuelto"}
        </button>
      )}
    </article>
  );
}
