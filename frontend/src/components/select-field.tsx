"use client";

import React from "react";

interface SelectFieldProps {
  label: string;
  name: string;
  options: Array<{ value: string; label: string }>;
  error?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  required?: boolean;
  placeholder?: string;
}

export function SelectField({
  label,
  name,
  options,
  error,
  value,
  onChange,
  required = false,
  placeholder = "Selecciona una opción",
}: SelectFieldProps) {
  const selectId = `select-${name}`;
  const errorId = `error-${name}`;

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={selectId}
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
      )}
      <select
        id={selectId}
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        className="rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
        style={
          error
            ? {
                borderColor: "var(--color-leather)",
                background: "var(--color-cream)",
                color: "var(--color-ink)",
              }
            : {
                borderColor: "var(--color-border)",
                background: "var(--color-cream)",
                color: "var(--color-ink)",
              }
        }
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
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
