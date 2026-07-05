import React from "react";
import { motion } from "motion/react";
import { Check } from "lucide-react";

export default function Checkbox({
  checked = false,
  onCheckedChange,
  disabled = false,
  label,
  error,
  className = "",
  id,
  ...props
}) {
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  const handleClick = () => {
    if (!disabled) {
      onCheckedChange?.(!checked);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <div className={`flex items-start gap-2.5 ${className}`} {...props}>
      <motion.button
        type="button"
        role="checkbox"
        id={checkboxId}
        aria-checked={checked}
        aria-disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        whileTap={!disabled ? { scale: 0.9 } : {}}
        className={`
          shrink-0 w-4 h-4 rounded border flex items-center justify-center
          transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent/20
          ${checked
            ? "bg-accent border-accent text-white"
            : "bg-bg border-border hover:border-accent/40"
          }
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        {checked && <Check size={12} strokeWidth={3} />}
      </motion.button>

      {label && (
        <label
          htmlFor={checkboxId}
          onClick={handleClick}
          className={`
            text-sm cursor-pointer select-none
            ${disabled ? "opacity-50 cursor-not-allowed" : "text-text"}
            ${error ? "text-danger" : ""}
          `}
        >
          {label}
        </label>
      )}

      {error && !label && (
        <span className="text-xs text-danger">{error}</span>
      )}
    </div>
  );
}