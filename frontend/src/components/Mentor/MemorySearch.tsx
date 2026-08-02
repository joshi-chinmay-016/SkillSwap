// src/components/Mentor/MemorySearch.tsx

import React from "react";
import { Search, X } from "lucide-react";

interface MemorySearchProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
}

export default function MemorySearch({
  value,
  onChange,
  placeholder = "Search memories...",
}: MemorySearchProps) {
  return (
    <div className="relative flex-1 min-w-[200px]">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-8 py-2 rounded-xl bg-bg border border-border text-xs text-text placeholder:text-text-secondary focus:outline-none focus:border-accent transition-colors"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 rounded-full hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
