"use client";

import React from "react";

interface CopyStatusBadgeProps {
  status: "available" | "on_loan";
  borrowerName?: string;
  loanDate?: string;
}

export function CopyStatusBadge({
  status,
  borrowerName,
  loanDate,
}: CopyStatusBadgeProps) {
  if (status === "available") {
    return (
      <span
        className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
        style={{ background: "#D8EDE1", color: "var(--color-reading)" }}
        aria-label="Estado: Disponible"
      >
        Disponible
      </span>
    );
  }

  const formattedDate = loanDate
    ? new Date(loanDate).toLocaleDateString("es-ES", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  return (
    <span
      className="inline-flex flex-col items-start rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ background: "#FAF0E8", color: "var(--color-leather)" }}
      aria-label={`Estado: Prestado a ${borrowerName ?? "desconocido"}`}
    >
      <span>Prestado a {borrowerName ?? "desconocido"}</span>
      {formattedDate && (
        <span
          className="text-[10px]"
          style={{ color: "var(--color-teak)" }}
        >
          {formattedDate}
        </span>
      )}
    </span>
  );
}
