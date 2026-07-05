import React from "react";

export default function Input({
  label,
  error,
  id,
  type = "text",
  disabled = false,
  className = "",
  ...props
}) {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`flex flex-col gap-1 w-full text-left ${className}`}>
      {label && (
        <label
          htmlFor={inputId}
          className="text-xs font-semibold text-text-secondary select-none"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        disabled={disabled}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${inputId}-error` : undefined}
        className={`w-full px-3 py-2 text-sm rounded-md border bg-bg text-text shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent disabled:opacity-50 disabled:bg-bg-alt ${
          error ? "border-danger focus:ring-danger/20 focus:border-danger" : "border-border"
        }`}
        {...props}
      />
      {error && (
        <span
          id={`${inputId}-error`}
          className="text-xs text-danger font-medium mt-0.5"
          role="alert"
        >
          {error}
        </span>
      )}
    </div>
  );
}
