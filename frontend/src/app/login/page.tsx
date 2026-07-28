"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { InputField } from "@/components/input-field";
import { ApiError } from "@/lib/api-client";

const ERROR_MESSAGES: Record<string, string> = {
  invalid_credentials: "Email o contraseña incorrectos.",
  email_already_exists: "Este email ya está registrado.",
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function LoginContent() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

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
      const redirect = searchParams.get("redirect") || "/dashboard";
      router.push(redirect);
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.detail === "object" && err.detail !== null
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
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{ background: "var(--color-parchment)" }}
    >
      <div
        className="w-full max-w-md rounded-xl p-8"
        style={{
          background: "var(--color-cream)",
          border: "1px solid var(--color-border)",
          boxShadow: "0 4px 24px -4px rgba(28, 16, 8, 0.14)",
        }}
      >
        {/* Logo */}
        <div className="mb-8 text-center">
          <h1
            className="text-3xl font-bold tracking-tight"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--color-walnut)",
            }}
          >
            EntreLíneas
          </h1>
          <p
            className="mt-1 text-[11px] tracking-widest uppercase"
            style={{ color: "var(--color-brass)" }}
          >
            biblioteca familiar
          </p>
        </div>

        {/* Heading */}
        <h2
          className="mb-6 text-center text-lg font-semibold"
          style={{ color: "var(--color-walnut)" }}
        >
          Iniciar sesión
        </h2>

        {/* Form-level error */}
        {formError && (
          <div
            className="mb-4 rounded-md px-4 py-3 text-sm"
            role="alert"
            style={{
              background: "#FAF0E8",
              border: "1px solid var(--color-leather)",
              color: "var(--color-leather)",
            }}
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
            className="mt-2 w-full rounded-full px-4 py-2.5 text-sm font-medium transition-colors focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
            style={{
              background: "var(--color-walnut)",
              color: "var(--color-cream)",
            }}
            onMouseEnter={(e) => {
              if (!isSubmitting)
                (e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-mahogany)";
            }}
            onMouseLeave={(e) => {
              if (!isSubmitting)
                (e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-walnut)";
            }}
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p
          className="mt-6 text-center text-sm"
          style={{ color: "var(--color-ink-faint)" }}
        >
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-medium transition-colors"
            style={{ color: "var(--color-teak)" }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLAnchorElement).style.color =
                "var(--color-mahogany)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLAnchorElement).style.color =
                "var(--color-teak)")
            }
          >
            Regístrate
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" style={{ background: "var(--color-parchment)" }} />}>
      <LoginContent />
    </Suspense>
  );
}
