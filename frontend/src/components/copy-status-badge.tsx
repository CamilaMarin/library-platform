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
        className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800"
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
      className="inline-flex flex-col items-start rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800"
      aria-label={`Estado: Prestado a ${borrowerName ?? "desconocido"}`}
    >
      <span>Prestado a {borrowerName ?? "desconocido"}</span>
      {formattedDate && (
        <span className="text-[10px] text-orange-600">{formattedDate}</span>
      )}
    </span>
  );
}
