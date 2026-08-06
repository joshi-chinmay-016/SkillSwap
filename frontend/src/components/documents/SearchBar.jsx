import React, { useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Search, X } from "lucide-react";

export default function SearchBar({ value, onChange }) {
  const inputRef = useRef(null);

  // Global shortcut ⌘K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const isMac = typeof window !== "undefined" && navigator.platform.toUpperCase().indexOf("MAC") >= 0;

  return (
    <div className="relative flex-1 min-w-[200px]">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-secondary">
        <Search size={16} />
      </div>

      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search documents... (press ⌘K)"
        className="w-full pl-9 pr-14 py-2 rounded-xl bg-bg-alt/80 border border-border/80 text-xs font-medium text-text placeholder:text-text-secondary/60 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/15 transition-all duration-150"
      />

      <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center gap-1">
        {value ? (
          <button
            type="button"
            onClick={() => onChange("")}
            className="p-1 rounded-md hover:bg-bg text-text-secondary hover:text-text cursor-pointer transition-colors"
            title="Clear search"
          >
            <X size={14} />
          </button>
        ) : (
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-border bg-bg text-[10px] font-semibold text-text-secondary pointer-events-none">
            {isMac ? "⌘K" : "Ctrl+K"}
          </kbd>
        )}
      </div>
    </div>
  );
}
