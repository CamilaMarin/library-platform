"use client";

import { useEffect, useState, useCallback } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { LoanCard } from "@/components/loan-card";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPatch, ApiError } from "@/lib/api-client";
import type { LoanWithDetails } from "@/types";

type TabStatus = "active" | "returned" | "borrowed";

const TABS: { id: TabStatus; label: string }[] = [
  { id: "active",   label: "Activos" },
  { id: "returned", label: "Historial" },
  { id: "borrowed", label: "Me prestaron" },
];

export default function LoansPage() {
  const [activeTab, setActiveTab] = useState<TabStatus>("active");
  const [loans, setLoans] = useState<LoanWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [returningLoanId, setReturningLoanId] = useState<string | null>(null);
  const { showToast } = useToast();

  const fetchLoans = useCallback(async (status: TabStatus) => {
    setLoading(true);
    try {
      let data: LoanWithDetails[];
      if (status === "borrowed") {
        data = await apiGet<LoanWithDetails[]>("/loans/borrowed?status=active");
      } else {
        data = await apiGet<LoanWithDetails[]>(`/loans?status=${status}`);
      }
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
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <h1
            className="text-2xl font-bold mb-6"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--color-walnut)",
            }}
          >
            Mis Préstamos
          </h1>

          {/* Tabs */}
          <div
            className="flex gap-1 mb-6 p-1 rounded-lg w-fit"
            style={{ background: "var(--color-aged)" }}
          >
            {TABS.map((tab) => {
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
                  style={
                    active
                      ? {
                          background: "var(--color-cream)",
                          color: "var(--color-walnut)",
                          boxShadow: "0 1px 3px rgba(28,16,8,0.12)",
                        }
                      : {
                          background: "transparent",
                          color: "var(--color-ink-soft)",
                        }
                  }
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Content */}
          {loading ? (
            <Skeleton variant="card" count={3} />
          ) : loans.length === 0 ? (
            <div
              className="rounded-lg p-8 text-center"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
              }}
            >
              <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                {activeTab === "active"
                  ? "No tienes préstamos activos."
                  : activeTab === "returned"
                  ? "No tienes préstamos devueltos."
                  : "No te han prestado libros."}
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {loans.map((loan) => (
                <LoanCard
                  key={loan.id}
                  loan={loan}
                  variant={activeTab === "borrowed" ? "active" : activeTab}
                  onReturn={activeTab === "active" ? handleReturn : undefined}
                  isReturning={returningLoanId === loan.id}
                  isBorrowedView={activeTab === "borrowed"}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
