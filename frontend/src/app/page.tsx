"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (isAuthenticated) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <main
      className="flex min-h-screen items-center justify-center"
      style={{ background: "var(--color-parchment)" }}
    >
      <div
        className="h-8 w-8 animate-spin rounded-full border-4"
        style={{
          borderColor: "var(--color-aged)",
          borderTopColor: "var(--color-teak)",
        }}
      />
    </main>
  );
}
