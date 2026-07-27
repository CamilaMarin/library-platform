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
        className="text-sm font-medium text-gray-700"
      >
        {label}
        {required && <span className="ml-1 text-red-500">*</span>}
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
        className={`rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-100 ${
          error
            ? "border-red-500 focus:ring-red-500"
            : "border-gray-300"
        }`}
      />
      {error && (
        <p id={errorId} className="text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
