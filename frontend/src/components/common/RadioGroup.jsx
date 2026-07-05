import React from "react";
import { motion } from "motion/react";

export default function RadioGroup({
  options = [],
  value,
  onChange,
  disabled = false,
  error,
  label,
  orientation = "vertical",
  className = "",
  name,
  ...props
}) {
  const groupName = name || `radiogroup-${Math.random().toString(36).substr(2, 9)}`;

  const handleSelect = (optionValue) => {
    if (!disabled) {
      onChange?.(optionValue);
    }
  };

  return (
    <div className={`flex flex-col gap-2 ${className}`} {...props}>
      {label && (
        <span className="text-xs font-semibold text-text-secondary">
          {label}
        </span>
      )}

      <div
        role="radiogroup"
        aria-label={label}
        className={`flex ${orientation === "horizontal" ? "flex-row flex-wrap gap-4" : "flex-col gap-2.5"}`}
      >
        {options.map((option) => (
          <div
            key={option.value}
            className="flex items-center gap-2.5"
          >
            <motion.button
              type="button"
              role="radio"
              aria-checked={option.value === value}
              aria-disabled={disabled || option.disabled}
              tabIndex={disabled || option.disabled ? -1 : 0}
              name={groupName}
              onClick={() => handleSelect(option.value)}
              disabled={disabled || option.disabled}
              whileTap={!disabled && !option.disabled ? { scale: 0.9 } : {}}
              className={`
                shrink-0 w-4 h-4 rounded-full border flex items-center justify-center
                transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent/20
                ${option.value === value
                  ? "border-accent"
                  : "border-border hover:border-accent/40"
                }
                ${(disabled || option.disabled) ? "opacity-50 cursor-not-allowed" : ""}
              `}
            >
              {option.value === value && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-2 h-2 rounded-full bg-accent"
                />
              )}
            </motion.button>

            <label
              className={`
                text-sm cursor-pointer select-none
                ${(disabled || option.disabled) ? "opacity-50 cursor-not-allowed" : "text-text"}
                ${error ? "text-danger" : ""}
              `}
            >
              {option.label}
            </label>
          </div>
        ))}
      </div>

      {error && (
        <p className="text-xs text-danger mt-0.5">{error}</p>
      )}
    </div>
  );
}