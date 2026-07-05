import React from "react";
import { motion } from "motion/react";

export default function ProgressBar({
  value = 0,
  max = 100,
  variant = "primary",
  size = "md",
  showLabel = false,
  animated = true,
  className = "",
  ...props
}) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const variants = {
    primary: "bg-accent",
    success: "bg-green-500",
    warning: "bg-yellow-500",
    danger: "bg-danger",
  };

  const sizes = {
    sm: "h-1",
    md: "h-2",
    lg: "h-3",
  };

  const trackStyles = "w-full bg-bg-alt border border-border rounded-full overflow-hidden";
  const fillStyles = `${variants[variant]} h-full rounded-full transition-all duration-300`;

  return (
    <div className={`flex flex-col gap-1 ${className}`} {...props}>
      <div className={trackStyles}>
        {animated ? (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={`${fillStyles} ${sizes[size]}`}
          />
        ) : (
          <div
            className={`${fillStyles} ${sizes[size]}`}
            style={{ width: `${percentage}%` }}
          />
        )}
      </div>

      {showLabel && (
        <div className="flex justify-between text-[10px] text-text-secondary">
          <span>{value}</span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
    </div>
  );
}