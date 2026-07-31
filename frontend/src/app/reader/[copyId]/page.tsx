"use client";

/**
 * Route: /reader/{copyId}
 * Protected route — renders the appropriate reader (EPUB or PDF) based on copy format.
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { apiGet } from "@/lib/api-client";
import { useAuth } from "@/context/auth-context";
import { EpubReader } from "@/components/epub-reader";
import { PdfReader } from "@/components/pdf-reader";

interface CopyInfo {
  id: string;
  format: string;  // "epub" | "pdf" | "physical"
  book_id: string;
  type: string;    // "digital" | "physical"
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ReaderPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const copyId = params.copyId as string;

  const [copyInfo, setCopyInfo] = useState<CopyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace(`/login?redirect=${encodeURIComponent(`/reader/${copyId}`)}`);
    }
  }, [authLoading, isAuthenticated, router, copyId]);

  // Fetch copy info to determine format
  useEffect(() => {
    if (!isAuthenticated || !copyId) return;

    async function fetchCopyInfo() {
      try {
        const data = await apiGet<CopyInfo>(`/copies/${copyId}`);
        setCopyInfo(data);
      } catch {
        setError("No se pudo cargar la información del archivo.");
      } finally {
        setLoading(false);
      }
    }

    fetchCopyInfo();
  }, [isAuthenticated, copyId]);

  const handleClose = () => {
    router.back();
  };

  if (authLoading || loading) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{ backgroundColor: "var(--color-parchment)" }}
      >
        <div className="flex flex-col items-center gap-3">
          <Loader2
            className="w-8 h-8 animate-spin"
            style={{ color: "var(--color-teak)" }}
          />
          <span className="text-sm" style={{ color: "var(--color-ink-soft)" }}>
            Preparando lector...
          </span>
        </div>
      </div>
    );
  }

  if (error || !copyInfo) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{ backgroundColor: "var(--color-parchment)" }}
      >
        <div className="text-center p-8">
          <p className="text-lg mb-4" style={{ color: "var(--color-ink)" }}>
            {error ?? "Archivo no encontrado."}
          </p>
          <button onClick={handleClose} className="btn-primary">
            Volver
          </button>
        </div>
      </div>
    );
  }

  // Determine format from copy info
  const isEpub = copyInfo.format === "epub";

  const isPdf = copyInfo.format === "pdf";

  const fileUrl = `${BASE_URL}/copies/${copyId}/file`;

  if (isEpub) {
    return <EpubReader copyId={copyId} fileUrl={fileUrl} onClose={handleClose} />;
  }

  if (isPdf) {
    return <PdfReader copyId={copyId} fileUrl={fileUrl} onClose={handleClose} />;
  }

  // Unsupported format
  return (
    <div
      className="flex min-h-screen items-center justify-center"
      style={{ backgroundColor: "var(--color-parchment)" }}
    >
      <div className="text-center p-8">
        <p className="text-lg mb-4" style={{ color: "var(--color-ink)" }}>
          Formato no soportado: {copyInfo.format}
        </p>
        <button onClick={handleClose} className="btn-primary">
          Volver
        </button>
      </div>
    </div>
  );
}
