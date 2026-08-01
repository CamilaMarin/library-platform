import { describe, it, expect } from "vitest";
import {
  validateName,
  validateEmail,
  validatePurpose,
  isRectificationFormValid,
  isOppositionFormValid,
} from "./settings-validation";

describe("validateName", () => {
  it("returns null for a valid name", () => {
    expect(validateName("María")).toBeNull();
  });

  it("returns error for empty string", () => {
    expect(validateName("")).toBe("El nombre es obligatorio");
  });

  it("returns error for whitespace-only string", () => {
    expect(validateName("   ")).toBe("El nombre es obligatorio");
  });

  it("returns null for a name at max length (200 chars)", () => {
    expect(validateName("a".repeat(200))).toBeNull();
  });

  it("returns error for a name over 200 chars (trimmed)", () => {
    expect(validateName("a".repeat(201))).toBe(
      "El nombre no puede superar los 200 caracteres"
    );
  });

  it("trims before checking length — valid at boundary", () => {
    // 200 chars + surrounding spaces — trimmed is 200, valid
    expect(validateName("  " + "a".repeat(200) + "  ")).toBeNull();
  });

  it("trims before checking length — invalid over boundary", () => {
    // 201 chars + surrounding spaces — trimmed is 201, invalid
    expect(validateName("  " + "a".repeat(201) + "  ")).toBe(
      "El nombre no puede superar los 200 caracteres"
    );
  });
});

describe("validateEmail", () => {
  it("returns null for a valid email", () => {
    expect(validateEmail("user@example.com")).toBeNull();
  });

  it("returns error for empty string", () => {
    expect(validateEmail("")).toBe("El correo es obligatorio");
  });

  it("returns error for email without @", () => {
    expect(validateEmail("userexample.com")).toBe("Formato de correo inválido");
  });

  it("returns error for email without domain part", () => {
    expect(validateEmail("user@")).toBe("Formato de correo inválido");
  });

  it("returns error for email without local part", () => {
    expect(validateEmail("@example.com")).toBe("Formato de correo inválido");
  });

  it("returns error for email with spaces", () => {
    expect(validateEmail("user @example.com")).toBe(
      "Formato de correo inválido"
    );
  });

  it("returns null for email at max length (320 chars)", () => {
    const local = "a".repeat(300);
    const email = `${local}@example.com`; // 312 chars
    expect(validateEmail(email)).toBeNull();
  });

  it("returns error for email over 320 chars", () => {
    const local = "a".repeat(310);
    const email = `${local}@example.com`; // 322 chars
    expect(validateEmail(email)).toBe(
      "El correo no puede superar los 320 caracteres"
    );
  });
});

describe("validatePurpose", () => {
  it("returns null for a valid purpose", () => {
    expect(validatePurpose("Recomendaciones de lectura")).toBeNull();
  });

  it("returns error for empty string", () => {
    expect(validatePurpose("")).toBe("El motivo es obligatorio");
  });

  it("returns error for whitespace-only string", () => {
    expect(validatePurpose("   ")).toBe("El motivo es obligatorio");
  });

  it("returns null for purpose at max length (200 chars)", () => {
    expect(validatePurpose("x".repeat(200))).toBeNull();
  });

  it("returns error for purpose over 200 chars (trimmed)", () => {
    expect(validatePurpose("x".repeat(201))).toBe(
      "El motivo no puede superar los 200 caracteres"
    );
  });
});

describe("isRectificationFormValid", () => {
  it("returns true when both name and email are valid", () => {
    expect(isRectificationFormValid("María", "maria@example.com")).toBe(true);
  });

  it("returns false when name is invalid", () => {
    expect(isRectificationFormValid("", "maria@example.com")).toBe(false);
  });

  it("returns false when email is invalid", () => {
    expect(isRectificationFormValid("María", "not-an-email")).toBe(false);
  });

  it("returns false when both are invalid", () => {
    expect(isRectificationFormValid("", "")).toBe(false);
  });
});

describe("isOppositionFormValid", () => {
  it("returns true when purpose is valid", () => {
    expect(isOppositionFormValid("Estadísticas de uso")).toBe(true);
  });

  it("returns false when purpose is empty", () => {
    expect(isOppositionFormValid("")).toBe(false);
  });

  it("returns false when purpose is whitespace-only", () => {
    expect(isOppositionFormValid("   ")).toBe(false);
  });
});
