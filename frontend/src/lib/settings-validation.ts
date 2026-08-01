/**
 * Pure validation functions for the Settings page forms.
 * Each function returns null if valid, or an error message string if invalid.
 */

// === Name validation ===

export function validateName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length === 0) {
    return "El nombre es obligatorio";
  }
  if (trimmed.length > 200) {
    return "El nombre no puede superar los 200 caracteres";
  }
  return null;
}

// === Email validation ===

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email: string): string | null {
  if (email.length === 0) {
    return "El correo es obligatorio";
  }
  if (email.length > 320) {
    return "El correo no puede superar los 320 caracteres";
  }
  if (!EMAIL_REGEX.test(email)) {
    return "Formato de correo inválido";
  }
  return null;
}

// === Purpose validation ===

export function validatePurpose(purpose: string): string | null {
  const trimmed = purpose.trim();
  if (trimmed.length === 0) {
    return "El motivo es obligatorio";
  }
  if (trimmed.length > 200) {
    return "El motivo no puede superar los 200 caracteres";
  }
  return null;
}

// === Form-level validity ===

export function isRectificationFormValid(name: string, email: string): boolean {
  return validateName(name) === null && validateEmail(email) === null;
}

export function isOppositionFormValid(purpose: string): boolean {
  return validatePurpose(purpose) === null;
}
