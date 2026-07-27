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
          className="text-sm font-medium text-gray-700"
        >
          Fecha estimada de devolución
        </label>
        <input
          id="estimated-return-date"
          type="date"
          name="estimatedReturnDate"
          value={estimatedReturnDate}
          onChange={(e) => setEstimatedReturnDate(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          disabled={submitting || !selectedBorrowerId}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Registrando..." : "Registrar préstamo"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
