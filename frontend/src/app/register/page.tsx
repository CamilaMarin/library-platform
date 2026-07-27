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
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
        <h1 className="mb-2 text-center text-2xl font-bold text-blue-700">
          EntreLíneas
        </h1>
        <h2 className="mb-6 text-center text-lg font-semibold text-gray-700">
          Crear cuenta
        </h2>

        {formError && (
          <div
            className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700"
            role="alert"
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

          <div className="flex flex-col gap-1">
            <label className="flex items-start gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                aria-describedby={errors.consent ? "error-consent" : undefined}
              />
              <span>
                Acepto la política de privacidad y el tratamiento de mis datos
                personales
              </span>
            </label>
            {errors.consent && (
              <p id="error-consent" className="text-xs text-red-600" role="alert">
                {errors.consent}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? "Registrando..." : "Registrarme"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          ¿Ya tienes cuenta?{" "}
          <Link
            href="/login"
            className="font-medium text-blue-600 hover:text-blue-700"
          >
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
