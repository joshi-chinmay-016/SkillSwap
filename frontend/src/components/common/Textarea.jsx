import React from "react";

export default function Textarea({
  label,
  error,
  id,
  rows = 4,
  disabled = false,
  className = "",
  ...props
}) {
  const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`flex flex-col gap-1 w-full text-left ${className}`}>
      {label && (
        <label
          htmlFor={textareaId}
          className="text-xs font-semibold text-text-secondary select-none"
        >
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        rows={rows}
        disabled={disabled}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${textareaId}-error` : undefined}
        className={`w-full px-3 py-2 text-sm rounded-md border bg-bg text-text shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent disabled:opacity-50 disabled:bg-bg-alt resize-y ${
          error ? "border-danger focus:ring-danger/20 focus:border-danger" : "border-border"
        }`}
        {...props}
      />
      {error && (
        <span
          id={`${textareaId}-error`}
          className="text-xs text-danger font-medium mt-0.5"
          role="alert"
        >
          {error}
        </span>
      )}
    </div>
  );
}
