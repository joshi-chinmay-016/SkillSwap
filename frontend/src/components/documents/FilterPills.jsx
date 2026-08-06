import React from "react";
import { motion } from "motion/react";

const FILTER_OPTIONS = [
  { id: "all", label: "All" },
  { id: "pdf", label: "PDF" },
  { id: "txt", label: "TXT" },
  { id: "md", label: "Markdown" },
];

export default function FilterPills({ selectedFilter, onSelectFilter }) {
  return (
    <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
      {FILTER_OPTIONS.map((option) => {
        const isSelected = selectedFilter === option.id;
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onSelectFilter(option.id)}
            className={`
              relative px-3 py-1.5 rounded-lg font-bold transition-all duration-150 cursor-pointer select-none
              ${
                isSelected
                  ? "text-indigo-600 dark:text-indigo-400 font-extrabold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-700/60"
              }
            `}
          >
            {isSelected && (
              <motion.div
                layoutId="activeFilterPill"
                className="absolute inset-0 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-xs"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10">{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
