import React from "react";
import { motion } from "motion/react";
import { LayoutGrid, List } from "lucide-react";

export default function ViewToggle({ viewMode, onChangeViewMode }) {
  return (
    <div className="flex items-center bg-bg-alt/80 p-1 rounded-xl border border-border/80 text-xs">
      <button
        type="button"
        onClick={() => onChangeViewMode("grid")}
        className={`
          relative p-1.5 rounded-lg text-text-secondary hover:text-text cursor-pointer transition-colors
          ${viewMode === "grid" ? "text-accent" : ""}
        `}
        title="Grid View"
      >
        {viewMode === "grid" && (
          <motion.div
            layoutId="activeViewMode"
            className="absolute inset-0 rounded-lg bg-bg border border-accent/20 shadow-xs"
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
          />
        )}
        <LayoutGrid size={15} className="relative z-10" />
      </button>

      <button
        type="button"
        onClick={() => onChangeViewMode("list")}
        className={`
          relative p-1.5 rounded-lg text-text-secondary hover:text-text cursor-pointer transition-colors
          ${viewMode === "list" ? "text-accent" : ""}
        `}
        title="List View"
      >
        {viewMode === "list" && (
          <motion.div
            layoutId="activeViewMode"
            className="absolute inset-0 rounded-lg bg-bg border border-accent/20 shadow-xs"
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
          />
        )}
        <List size={15} className="relative z-10" />
      </button>
    </div>
  );
}
