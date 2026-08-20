import React from "react";
import { motion } from "motion/react";

export default function SectionHeader({
  badge,
  badgeIcon: BadgeIcon,
  title,
  subtitle,
  actions,
  handwrittenNote,
  className = "",
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-border/70 ${className}`}
    >
      <div className="space-y-1 text-left">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          {badge && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-950/80 border border-yellow-300 dark:border-yellow-700 text-amber-900 dark:text-amber-300 text-[11px] font-bold tracking-wide uppercase shadow-xs">
              {BadgeIcon && <BadgeIcon size={12} className="shrink-0 text-amber-600 dark:text-amber-400" />}
              <span>{badge}</span>
            </div>
          )}
          {handwrittenNote && (
            <span className="font-handwriting text-base font-bold text-rose-500 rotate-[-2deg] inline-block">
              {handwrittenNote}
            </span>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-text">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs sm:text-sm text-text-secondary max-w-2xl">
            {subtitle}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex items-center gap-3 shrink-0 flex-wrap">
          {actions}
        </div>
      )}
    </motion.div>
  );
}
