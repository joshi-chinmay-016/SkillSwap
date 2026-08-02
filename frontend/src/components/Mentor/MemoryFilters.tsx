// src/components/Mentor/MemoryFilters.tsx

import React from "react";

export const MEMORY_CATEGORIES = [
  { id: "ALL", label: "All Memories" },
  { id: "LEARNING_STYLE", label: "Learning Style" },
  { id: "LONG_TERM_GOAL", label: "Goals" },
  { id: "STRONG_TOPIC", label: "Strong Topics" },
  { id: "WEAK_TOPIC", label: "Weak Topics" },
  { id: "LEARNING_PREFERENCE", label: "Preferences" },
  { id: "ACHIEVEMENT", label: "Achievements" },
  { id: "GENERAL", label: "General" },
];

interface MemoryFiltersProps {
  activeCategory: string;
  onSelectCategory: (category: string) => void;
  statusFilter: string;
  onSelectStatus: (status: string) => void;
}

export default function MemoryFilters({
  activeCategory,
  onSelectCategory,
  statusFilter,
  onSelectStatus,
}: MemoryFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      {/* Category Pills Scrollable */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        {MEMORY_CATEGORIES.map((cat) => {
          const isActive = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelectCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                isActive
                  ? "bg-accent text-white shadow-xs"
                  : "bg-bg border border-border text-text-secondary hover:text-text hover:bg-bg-alt"
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Active vs Archived Segmented Control */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-text-secondary font-medium">View:</span>
        <div className="inline-flex p-0.5 rounded-lg bg-bg-alt border border-border text-xs">
          <button
            type="button"
            onClick={() => onSelectStatus("ACTIVE")}
            className={`px-2.5 py-1 rounded-md font-semibold transition-all cursor-pointer ${
              statusFilter === "ACTIVE"
                ? "bg-bg text-accent shadow-xs"
                : "text-text-secondary hover:text-text"
            }`}
          >
            Active
          </button>
          <button
            type="button"
            onClick={() => onSelectStatus("ARCHIVED")}
            className={`px-2.5 py-1 rounded-md font-semibold transition-all cursor-pointer ${
              statusFilter === "ARCHIVED"
                ? "bg-bg text-amber-500 shadow-xs"
                : "text-text-secondary hover:text-text"
            }`}
          >
            Archived
          </button>
        </div>
      </div>
    </div>
  );
}
