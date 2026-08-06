import React from "react";
import { motion } from "motion/react";

/**
 * Circular progress ring displaying percentage and smooth SVG stroke animation.
 */
export default function ProgressRing({ progress = 0, size = 48, strokeWidth = 4, status = "PROCESSING" }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const isComplete = status === "READY" || progress >= 100;
  const isFailed = status === "FAILED";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background Circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-border/40 fill-none"
        />

        {/* Animated Progress Circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          strokeLinecap="round"
          className={`fill-none ${
            isFailed
              ? "text-danger"
              : isComplete
              ? "text-emerald-500"
              : "text-primary"
          }`}
        />
      </svg>

      {/* Center Percentage Label */}
      <span className="absolute text-[10px] font-bold text-text tracking-tighter">
        {isFailed ? "!" : isComplete ? "100%" : `${Math.round(progress)}%`}
      </span>
    </div>
  );
}
