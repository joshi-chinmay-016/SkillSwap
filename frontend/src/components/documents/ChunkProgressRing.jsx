import React from "react";
import { motion } from "motion/react";

export default function ChunkProgressRing({
  progress = 0, // 0 to 100
  size = 64,
  strokeWidth = 6,
  label = null,
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-200 dark:text-slate-800 fill-none"
        />
        {/* Animated Progress Ring */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          strokeLinecap="round"
          className="text-indigo-600 dark:text-indigo-400 fill-none"
        />
      </svg>

      {/* Label inside ring */}
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-xs font-black text-slate-900 dark:text-white">
          {label !== null ? label : `${Math.round(progress)}%`}
        </span>
      </div>
    </div>
  );
}
