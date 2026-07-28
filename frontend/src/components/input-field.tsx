"use client";

import React from "react";

interface InputFieldProps {
  label: string;
  name: string;
  type?: "text" | "email" | "password" | "number";
  error?: string;
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
  disabled?: boolean;
}

export function InputField({
  label,
  name,
  type = "text",
  error,
  placeholder,
  value,
  onChange,
  required = false,
  disabled = false,
}: InputFieldProps) {
  const inputId = `input-${name}`;
  const errorId = `error-${name}`;

  return (
    <div className="flex flex-col gap-1">
      <label
        htmlFor={inputId}
        className="text-sm font-medium"
        style={{ color: "var(--color-ink-soft)" }}
      >
        {label}
        {required && (
          <span className="ml-1" style={{ color: "var(--color-leather)" }}>
            *
          </span>
        )}
      </label>
      <input
        id={inputId}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        className="rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none disabled:cursor-not-allowed"
        style={
          error
            ? {
                borderColor: "var(--color-leather)",
                background: "var(--color-cream)",
                color: "var(--color-ink)",
                outlineColor: "var(--color-leather)",
              }
            : {
                borderColor: "var(--color-border)",
                background: "var(--color-cream)",
                color: "var(--color-ink)",
              }
        }
      />
      {error && (
        <p
          id={errorId}
          className="text-xs"
          style={{ color: "var(--color-leather)" }}
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
}
