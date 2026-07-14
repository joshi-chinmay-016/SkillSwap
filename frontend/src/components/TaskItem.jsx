import React from "react";
import { motion } from "motion/react";
import { CheckCircle, Circle, Clock } from "lucide-react";

/**
 * Interactive journey task item.
 * When onToggle is provided, renders as a clickable checkbox that
 * calls PATCH /journeys/tasks/{id}/toggle via the parent.
 * When onToggle is absent, renders as a static display item (backward-compatible).
 */
export default function TaskItem({ task, onToggle, isToggling = false }) {
  const { id, title, description, is_completed, completed_at } = task || {};

  const handleToggle = () => {
    if (onToggle && !isToggling) {
      onToggle(id, !is_completed);
    }
  };

  const isInteractive = typeof onToggle === "function";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`
        flex items-start gap-3 p-3 border rounded-lg transition-all duration-200
        ${is_completed
          ? "bg-success/[0.04] border-success/20"
          : "bg-bg border-border/40 hover:border-border"
        }
        ${isInteractive && !isToggling ? "cursor-pointer" : ""}
        ${isToggling ? "opacity-60 pointer-events-none" : ""}
      `}
      onClick={isInteractive ? handleToggle : undefined}
      role={isInteractive ? "button" : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onKeyDown={isInteractive ? (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleToggle();
        }
      } : undefined}
    >
      {/* Checkbox / Status Icon */}
      <div className="mt-0.5 flex-shrink-0">
        {isToggling ? (
          <div className="w-[18px] h-[18px] rounded-full border-2 border-accent/40 border-t-accent animate-spin" />
        ) : is_completed ? (
          <motion.div
            initial={{ scale: 0.5 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 400, damping: 15 }}
          >
            <CheckCircle className="text-success" size={18} />
          </motion.div>
        ) : (
          <Circle className="text-text-secondary/50" size={18} />
        )}
      </div>

      {/* Task Content */}
      <div className="flex-1 min-w-0">
        <h4
          className={`font-medium text-sm transition-colors duration-200 ${
            is_completed
              ? "text-text-secondary line-through decoration-success/40"
              : "text-text"
          }`}
          title={title}
        >
          {title}
        </h4>

        {description && (
          <p
            className={`text-xs mt-0.5 transition-colors duration-200 ${
              is_completed ? "text-text-secondary/60" : "text-text-secondary"
            }`}
            title={description}
          >
            {description}
          </p>
        )}

        {/* Completed timestamp */}
        {is_completed && completed_at && (
          <p className="flex items-center gap-1 text-[10px] text-success/70 mt-1.5 font-medium">
            <Clock size={10} />
            Completed {new Date(completed_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        )}
      </div>
    </motion.div>
  );
}
