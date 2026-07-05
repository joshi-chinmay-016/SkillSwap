import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Search, X, Loader2 } from "lucide-react";

export default function SearchBar({
  value = "",
  onChange,
  placeholder = "Search...",
  disabled = false,
  isLoading = false,
  onSearch,
  debounceMs = 300,
  className = "",
  size = "md",
  ...props
}) {
  const [localValue, setLocalValue] = useState(value);
  const [isFocused, setIsFocused] = useState(false);
  const timeoutRef = useRef(null);
  const inputRef = useRef(null);

  const sizes = {
    sm: "px-2.5 py-1.5 text-xs gap-1.5",
    md: "px-3 py-2 text-sm gap-2",
    lg: "px-4 py-2.5 text-base gap-2.5",
  };

  // Debounced search
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (onSearch && localValue !== value) {
      timeoutRef.current = setTimeout(() => {
        onSearch(localValue);
      }, debounceMs);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [localValue, debounceMs, onSearch]);

  // Sync with external value changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    onChange?.(newValue);
  };

  const handleClear = () => {
    setLocalValue("");
    onChange?.("");
    onSearch?.("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      onSearch?.(localValue);
      inputRef.current?.blur();
    }
    if (e.key === "Escape") {
      handleClear();
      inputRef.current?.blur();
    }
  };

  return (
    <div
      className={`
        relative flex items-center bg-bg border rounded-md transition-all
        focus-within:ring-2 focus-within:ring-accent/20
        ${isFocused ? "border-accent shadow-sm" : "border-border hover:border-accent/40"}
        ${disabled ? "opacity-50 cursor-not-allowed bg-bg-alt" : ""}
        ${sizes[size]}
        ${className}
      `}
    >
      <Search
        size={size === "sm" ? 14 : size === "md" ? 16 : 18}
        className="text-text-secondary shrink-0"
      />

      <input
        ref={inputRef}
        type="text"
        value={localValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 bg-transparent text-text placeholder:text-text-secondary outline-none min-w-0"
        {...props}
      />

      {isLoading && (
        <Loader2 size={14} className="text-text-secondary animate-spin shrink-0" />
      )}

      {localValue && !isLoading && (
        <motion.button
          type="button"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          exit={{ scale: 0 }}
          onClick={handleClear}
          disabled={disabled}
          className="p-0.5 rounded-full hover:bg-bg-alt text-text-secondary hover:text-text transition-colors cursor-pointer shrink-0"
          aria-label="Clear search"
        >
          <X size={12} />
        </motion.button>
      )}
    </div>
  );
}