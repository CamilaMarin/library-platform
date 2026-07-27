"use client";

import { useEffect, useState, useCallback } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { LoanCard } from "@/components/loan-card";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPatch, ApiError } from "@/lib/api-client";
import type { LoanWithDetails } from "@/types";

type TabStatus = "active" | "returned";

export default function LoansPage() {
  const [activeTab, setActiveTab] = useState<TabStatus>("active");
  const [loans, setLoans] = useState<LoanWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [returningLoanId, setReturningLoanId] = useState<string | null>(null);
  const { showToast } = useToast();

  const fetchLoans = useCallback(async (status: TabStatus) => {
    setLoading(true);
    try {
      const data = await apiGet<LoanWithDetails[]>(`/loans?status=${status}`);
      setLoans(data);
    } catch {
      setLoans([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLoans(activeTab);
  }, [activeTab, fetchLoans]);

  const handleTabChange = (tab: TabStatus) => {
    setActiveTab(tab);
  };

  const handleReturn = async (loanId: string) => {
    setReturningLoanId(loanId);
    try {
      await apiPatch(`/loans/${loanId}/return`);
      showToast("Préstamo devuelto", "success");
      fetchLoans(activeTab);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        showToast("Préstamo no encontrado.", "error");
      }
    } finally {
      setReturningLoanId(null);
    }
  };

  return (
    <ProtectedRoute>
      <Navigation />
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Mis Préstamos
          </h1>

          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              type="button"
              onClick={() => handleTabChange("active")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === "active"
                  ? "bg-blue-600 text-white"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-100"
              }`}
            >
              Activos
            </button>
            <button
              type="button"
              onClick={() => handleTabChange("returned")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === "returned"
                  ? "bg-blue-600 text-white"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-100"
              }`}
            >
              Historial
            </button>
          </div>

          {/* Content */}
          {loading ? (
            <Skeleton variant="card" count={3} />
          ) : loans.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              {activeTab === "active"
                ? "No tienes préstamos activos."
                : "No tienes préstamos devueltos."}
            </p>
          ) : (
            <div className="flex flex-col gap-4">
              {loans.map((loan) => (
                <LoanCard
                  key={loan.id}
                  loan={loan}
                  variant={activeTab}
                  onReturn={activeTab === "active" ? handleReturn : undefined}
                  isReturning={returningLoanId === loan.id}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
