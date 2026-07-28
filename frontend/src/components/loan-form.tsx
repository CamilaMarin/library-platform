"use client";

import React, { useState } from "react";
import { GroupMember, CreateLoanRequest, Loan } from "@/types";
import { apiPost, ApiError } from "@/lib/api-client";
import { useToast } from "@/context/toast-context";
import { SelectField } from "@/components/select-field";

interface LoanFormProps {
  copyId: string;
  groupMembers: GroupMember[];
  onSuccess: () => void;
  onCancel: () => void;
}

export function LoanForm({
  copyId,
  groupMembers,
  onSuccess,
  onCancel,
}: LoanFormProps) {
  const { showToast } = useToast();
  const [selectedBorrowerId, setSelectedBorrowerId] = useState("");
  const [estimatedReturnDate, setEstimatedReturnDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const today = new Date().toISOString().split("T")[0];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBorrowerId) return;

    setSubmitting(true);

    const payload: CreateLoanRequest = {
      borrower_user_id: selectedBorrowerId,
    };
    if (estimatedReturnDate) {
      payload.estimated_return_date = estimatedReturnDate;
    }

    try {
      await apiPost<Loan>(`/copies/${copyId}/loans`, payload);
      showToast("Préstamo registrado", "success");
      onSuccess();
    } catch (error) {
      if (error instanceof ApiError) {
        const detail =
          typeof error.detail === "string"
            ? error.detail
            : JSON.stringify(error.detail);

        if (detail === "copy_already_on_loan") {
          showToast("Esta copia ya está prestada.", "error");
        } else if (detail === "invalid_copy_type") {
          showToast("Solo se pueden prestar copias físicas.", "error");
        } else if (detail === "estimated_return_date_in_past") {
          showToast("La fecha de devolución no puede ser en el pasado.", "error");
        } else {
          showToast(detail, "error");
        }
      }
    } finally {
      setSubmitting(false);
    }
  };

  const borrowerOptions = groupMembers.map((member) => ({
    value: member.user_id,
    label: member.name,
  }));

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <SelectField
        label="Prestatario"
        name="borrower"
        options={borrowerOptions}
        value={selectedBorrowerId}
        onChange={(e) => setSelectedBorrowerId(e.target.value)}
        required
        placeholder="Selecciona un miembro"
      />

      <div className="flex flex-col gap-1">
        <label
          htmlFor="estimated-return-date"
          className="text-sm font-medium"
          style={{ color: "var(--color-ink-soft)" }}
        >
          Fecha estimada de devolución
        </label>
        <input
          id="estimated-return-date"
          type="date"
          name="estimatedReturnDate"
          value={estimatedReturnDate}
          onChange={(e) => setEstimatedReturnDate(e.target.value)}
          min={today}
          className="rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
          style={{
            borderColor: "var(--color-border)",
            background: "var(--color-cream)",
            color: "var(--color-ink)",
          }}
        />
      </div>

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          disabled={submitting || !selectedBorrowerId}
          className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
          onMouseEnter={(e) => {
            if (!submitting && selectedBorrowerId)
              (e.currentTarget as HTMLButtonElement).style.background =
                "var(--color-mahogany)";
          }}
          onMouseLeave={(e) => {
            if (!submitting && selectedBorrowerId)
              (e.currentTarget as HTMLButtonElement).style.background =
                "var(--color-walnut)";
          }}
        >
          {submitting ? "Registrando..." : "Registrar préstamo"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
          style={{
            border: "1px solid var(--color-border)",
            color: "var(--color-ink-soft)",
            background: "transparent",
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.background =
              "var(--color-parchment)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.background =
              "transparent")
          }
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
