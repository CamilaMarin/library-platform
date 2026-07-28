"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { useToast } from "@/context/toast-context";
import { InputField } from "@/components/input-field";
import { ApiError } from "@/lib/api-client";

const ERROR_MESSAGES: Record<string, string> = {
  email_already_exists: "Este email ya está registrado.",
  consent_required: "Debes aceptar la política de privacidad.",
  invalid_email: "El formato del email no es válido.",
  password_too_short: "La contraseña debe tener al menos 8 caracteres.",
};

export default function RegisterPage() {
  const { register } = useAuth();
  const { showToast } = useToast();
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [consent, setConsent] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!name.trim() || name.trim().length < 2) {
      newErrors.name = "El nombre debe tener al menos 2 caracteres.";
    }

    if (!email.trim()) {
      newErrors.email = "El email es obligatorio.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "El formato del email no es válido.";
    }

    if (!password) {
      newErrors.password = "La contraseña es obligatoria.";
    } else if (password.length < 8) {
      newErrors.password = "La contraseña debe tener al menos 8 caracteres.";
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = "Las contraseñas no coinciden.";
    }

    if (!consent) {
      newErrors.consent = "Debes aceptar la política de privacidad.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError("");

    if (!validate()) return;

    setIsSubmitting(true);

    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
        consent_policy_version: "1.0",
        consent_purpose: "account_creation",
      });

      showToast("Cuenta creada exitosamente. Inicia sesión.", "success");
      router.push("/login");
    } catch (err) {
      if (err instanceof ApiError) {
        if (typeof err.detail === "string") {
          const mapped = ERROR_MESSAGES[err.detail];
          setFormError(mapped ?? err.detail);
        } else if (typeof err.detail === "object") {
          const fieldErrors: Record<string, string> = {};
          for (const [key, value] of Object.entries(err.detail)) {
            fieldErrors[key] = ERROR_MESSAGES[value] ?? value;
          }
          setErrors(fieldErrors);
        }
      } else {
        setFormError("Ocurrió un error inesperado. Intenta de nuevo.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="flex min-h-screen items-center justify-center px-4 py-8"
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
        <div className="mb-6 text-center">
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

        <h2
          className="mb-6 text-center text-lg font-semibold"
          style={{ color: "var(--color-walnut)" }}
        >
          Crear cuenta
        </h2>

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

        <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
          <InputField
            label="Nombre"
            name="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={errors.name}
            required
            placeholder="Tu nombre"
          />

          <InputField
            label="Email"
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            required
            placeholder="correo@ejemplo.com"
          />

          <InputField
            label="Contraseña"
            name="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            required
            placeholder="Mínimo 8 caracteres"
          />

          <InputField
            label="Confirmar contraseña"
            name="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            required
            placeholder="Repite tu contraseña"
          />

          {/* Consent checkbox */}
          <div className="flex flex-col gap-1">
            <label
              className="flex items-start gap-2 text-sm cursor-pointer"
              style={{ color: "var(--color-ink-soft)" }}
            >
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded"
                style={{ accentColor: "var(--color-teak)" }}
                aria-describedby={errors.consent ? "error-consent" : undefined}
              />
              <span>
                Acepto la{" "}
                <a
                  href="/privacy"
                  target="_blank"
                  className="transition-colors"
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
                  política de privacidad
                </a>{" "}
                y el tratamiento de mis datos personales
              </span>
            </label>
            {errors.consent && (
              <p
                id="error-consent"
                className="text-xs"
                style={{ color: "var(--color-leather)" }}
                role="alert"
              >
                {errors.consent}
              </p>
            )}
          </div>

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
            {isSubmitting ? "Registrando..." : "Registrarme"}
          </button>
        </form>

        <p
          className="mt-4 text-center text-sm"
          style={{ color: "var(--color-ink-faint)" }}
        >
          ¿Ya tienes cuenta?{" "}
          <Link
            href="/login"
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
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
