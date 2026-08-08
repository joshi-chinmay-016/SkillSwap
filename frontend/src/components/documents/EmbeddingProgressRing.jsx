import React from "react";
import { motion } from "motion/react";

export default function EmbeddingProgressRing({
  progress = 0,
  size = 64,
  strokeWidth = 6,
  status = "PROCESSING",
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedProgress = Math.min(Math.max(progress, 0), 100);
  const strokeDashoffset = circumference - (normalizedProgress / 100) * circumference;

  let strokeColor = "stroke-indigo-600 dark:stroke-indigo-400";
  if (status === "READY" || normalizedProgress === 100) {
    strokeColor = "stroke-emerald-500 dark:stroke-emerald-400";
  } else if (status === "FAILED") {
    strokeColor = "stroke-red-500 dark:stroke-red-400";
  }

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
      role="progressbar"
      aria-valuenow={Math.round(normalizedProgress)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Embedding generation progress: ${Math.round(normalizedProgress)}%`}
    >
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className="stroke-slate-200 dark:stroke-slate-700/60"
          strokeWidth={strokeWidth}
          fill="transparent"
        />

        {/* Progress bar */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className={`${strokeColor} transition-colors duration-300`}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          strokeLinecap="round"
          fill="transparent"
        />
      </svg>

      {/* Centered label */}
      <span className="absolute text-xs font-black text-slate-800 dark:text-slate-100">
        {Math.round(normalizedProgress)}%
      </span>
    </div>
  );
}
