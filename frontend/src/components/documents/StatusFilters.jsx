import React from "react";
import { motion } from "motion/react";

const STATUS_OPTIONS = [
  { id: "all", label: "All Documents" },
  { id: "READY", label: "Ready" },
  { id: "PROCESSING", label: "Parsing" },
  { id: "UPLOADED", label: "Uploaded" },
  { id: "FAILED", label: "Failed" },
];

export default function StatusFilters({ selectedStatus, onStatusChange }) {
  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
      {STATUS_OPTIONS.map((option) => {
        const isActive = selectedStatus === option.id;

        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onStatusChange(option.id)}
            className={`relative px-3.5 py-1.5 rounded-xl text-xs font-bold tracking-wide transition-all duration-150 cursor-pointer whitespace-nowrap select-none ${
              isActive
                ? "bg-indigo-600 dark:bg-indigo-500 text-white shadow-sm font-extrabold"
                : "bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200/80 dark:border-slate-700/80"
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="status-filter-active-indicator"
                className="absolute inset-0 rounded-xl bg-indigo-600 dark:bg-indigo-500 shadow-sm -z-10"
                transition={{ type: "spring", stiffness: 350, damping: 25 }}
              />
            )}
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
