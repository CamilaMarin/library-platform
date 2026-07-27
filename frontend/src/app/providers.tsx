"use client";

import { AuthProvider } from "@/context/auth-context";
import { ToastProvider } from "@/context/toast-context";
import { ToastContainer } from "@/components/toast";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ToastProvider>
        {children}
        <ToastContainer />
      </ToastProvider>
    </AuthProvider>
  );
}
