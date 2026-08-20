import React from "react";
import { motion } from "motion/react";
import { FolderOpen } from "lucide-react";
import Button from "./Button";

export default function EmptyState({
  icon: Icon = FolderOpen,
  title = "No data found",
  description = "There is currently no information available for this section.",
  actionLabel,
  onAction,
  actionIcon,
  secondaryActionLabel,
  onSecondaryAction,
  className = "",
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`rounded-2xl border border-dashed border-border/80 bg-bg/50 p-8 sm:p-12 text-center flex flex-col items-center justify-center max-w-lg mx-auto ${className}`}
    >
      <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent mb-4 shadow-xs">
        <Icon size={26} className="shrink-0" />
      </div>

      <h3 className="text-base sm:text-lg font-semibold text-text mb-1 tracking-tight">
        {title}
      </h3>

      <p className="text-xs sm:text-sm text-text-secondary mb-6 max-w-sm leading-relaxed">
        {description}
      </p>

      <div className="flex items-center gap-3 flex-wrap justify-center">
        {secondaryActionLabel && (
          <Button variant="outline" size="sm" onClick={onSecondaryAction}>
            {secondaryActionLabel}
          </Button>
        )}
        {actionLabel && (
          <Button
            variant="primary"
            size="sm"
            onClick={onAction}
            rightIcon={actionIcon}
          >
            {actionLabel}
          </Button>
        )}
      </div>
    </motion.div>
  );
}
