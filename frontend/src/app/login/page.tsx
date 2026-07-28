"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { InputField } from "@/components/input-field";
import { ApiError } from "@/lib/api-client";

// === Error message mapping (Spanish) ===

const ERROR_MESSAGES: Record<string, string> = {
  invalid_credentials: "Email o contraseña incorrectos.",
  email_already_exists: "Este email ya está registrado.",
};

// === Simple email regex ===

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!email.trim()) {
      newErrors.email = "El email es obligatorio.";
    } else if (!EMAIL_REGEX.test(email.trim())) {
      newErrors.email = "El formato del email no es válido.";
    }

    if (!password) {
      newErrors.password = "La contraseña es obligatoria.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    setErrors({});

    if (!validate()) return;

    setIsSubmitting(true);

    try {
      await login(email.trim(), password);

      // On success: redirect to intended destination or dashboard
      const redirect = searchParams.get("redirect") || "/dashboard";
      router.push(redirect);
    } catch (err) {
      if (err instanceof ApiError) {
        // Backend returns {detail: "error_code"} — extract the detail string
        const detail = typeof err.detail === "object" && err.detail !== null
          ? (err.detail as Record<string, string>).detail ?? JSON.stringify(err.detail)
          : String(err.detail);
        const message = ERROR_MESSAGES[detail] ?? detail;
        setFormError(message);
      } else {
        setFormError("Ocurrió un error inesperado. Intenta de nuevo.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
        {/* Logo / App name */}
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-blue-700">EntreLíneas</h1>
        </div>

        {/* Heading */}
        <h2 className="mb-6 text-center text-xl font-semibold text-gray-800">
          Iniciar sesión
        </h2>

        {/* Form-level error banner */}
        {formError && (
          <div
            className="mb-4 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
            role="alert"
          >
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <InputField
            label="Email"
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            placeholder="tu@email.com"
            required
            disabled={isSubmitting}
          />

          <InputField
            label="Contraseña"
            name="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            placeholder="••••••••"
            required
            disabled={isSubmitting}
          />

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
        </form>

        {/* Register link */}
        <p className="mt-6 text-center text-sm text-gray-600">
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-medium text-blue-600 hover:text-blue-700 hover:underline"
          >
            Regístrate
          </Link>
        </p>
      </div>
    </div>
  );
}
