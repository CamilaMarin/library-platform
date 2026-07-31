"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { apiGet, apiPut, ApiError } from "@/lib/api-client";

interface ReadingProgress {
  position: string;
  percentage: number;
  file_format: string;
  last_read_at: string;
}

interface UseReadingProgressReturn {
  currentProgress: ReadingProgress | null;
  saveProgress: (position: string, percentage: number, fileFormat: string) => void;
  loading: boolean;
}

const DEBOUNCE_MS = 5000;

/**
 * Hook that fetches and auto-saves reading progress for a given copy.
 * - Fetches progress on mount via GET /copies/{copyId}/progress
 * - Exposes saveProgress(position, percentage, fileFormat) via PUT /copies/{copyId}/progress
 * - Debounces saves (max every 5 seconds)
 */
export function useReadingProgress(copyId: string): UseReadingProgressReturn {
  const [currentProgress, setCurrentProgress] = useState<ReadingProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const lastSaveRef = useRef<number>(0);
  const pendingRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch existing progress on mount
  useEffect(() => {
    let cancelled = false;

    async function fetchProgress() {
      try {
        const data = await apiGet<ReadingProgress>(`/copies/${copyId}/progress`);
        if (!cancelled) {
          setCurrentProgress(data);
        }
      } catch (err) {
        // 404 means no progress saved yet — that's fine
        if (err instanceof ApiError && err.status === 404) {
          // No progress yet
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchProgress();

    return () => {
      cancelled = true;
    };
  }, [copyId]);

  // Cleanup pending timer on unmount
  useEffect(() => {
    return () => {
      if (pendingRef.current) {
        clearTimeout(pendingRef.current);
      }
    };
  }, []);

  const saveProgress = useCallback(
    (position: string, percentage: number, fileFormat: string) => {
      const now = Date.now();
      const timeSinceLastSave = now - lastSaveRef.current;

      const doSave = async () => {
        lastSaveRef.current = Date.now();
        try {
          const data = await apiPut<ReadingProgress>(`/copies/${copyId}/progress`, {
            position,
            percentage,
            file_format: fileFormat,
          });
          setCurrentProgress(data);
        } catch {
          // Silently fail on save — will retry on next relocation
        }
      };

      // Clear any pending debounced save
      if (pendingRef.current) {
        clearTimeout(pendingRef.current);
        pendingRef.current = null;
      }

      if (timeSinceLastSave >= DEBOUNCE_MS) {
        doSave();
      } else {
        // Schedule save after remaining debounce time
        pendingRef.current = setTimeout(doSave, DEBOUNCE_MS - timeSinceLastSave);
      }
    },
    [copyId]
  );

  return { currentProgress, saveProgress, loading };
}
