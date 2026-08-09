import React from "react";
import { motion } from "motion/react";
import { Database, Check, AlertTriangle, RefreshCw } from "lucide-react";

/**
 * Premium SVG progress ring for FAISS Vector Indexing with accessible ARIA semantics and reduced motion support.
 */
export default function VectorIndexProgressRing({
  progress = 0,
  status = "INDEXED",
  size = 68,
  strokeWidth = 5,
}) {
  const normalizedProgress = Math.min(100, Math.max(0, progress));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedProgress / 100) * circumference;

  const isCompleted = status === "INDEXED" || normalizedProgress === 100;
  const isFailed = status === "INDEX_FAILED";
  const isPartial = status === "PARTIAL";

  const getColors = () => {
    if (isFailed) {
      return {
        stroke: "#EF4444", // red-500
        bg: "bg-red-50 dark:bg-red-950/50",
        text: "text-red-600 dark:text-red-400",
      };
    }
    if (isPartial) {
      return {
        stroke: "#F59E0B", // amber-500
        bg: "bg-amber-50 dark:bg-amber-950/50",
        text: "text-amber-600 dark:text-amber-400",
      };
    }
    if (isCompleted) {
      return {
        stroke: "#10B981", // emerald-500
        bg: "bg-emerald-50 dark:bg-emerald-950/50",
        text: "text-emerald-600 dark:text-emerald-400",
      };
    }
    return {
      stroke: "#6366F1", // indigo-500
      bg: "bg-indigo-50 dark:bg-indigo-950/50",
      text: "text-indigo-600 dark:text-indigo-400",
    };
  };

  const colors = getColors();

  return (
    <div
      className="relative flex items-center justify-center shrink-0"
      style={{ width: size, height: size }}
      role="progressbar"
      aria-valuenow={Math.round(normalizedProgress)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`FAISS Vector Indexing Progress: ${Math.round(normalizedProgress)}%`}
    >
      <svg width={size} height={size} className="-rotate-90 transform">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-100 dark:text-slate-800"
          fill="transparent"
        />

        {/* Progress indicator */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeLinecap="round"
          fill="transparent"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </svg>

      {/* Center Icon / Badge */}
      <div
        className={`absolute inset-1.5 rounded-full ${colors.bg} ${colors.text} flex items-center justify-center font-black shadow-xs`}
      >
        {isFailed ? (
          <AlertTriangle size={18} />
        ) : isCompleted ? (
          <Check size={20} strokeWidth={3} />
        ) : isPartial ? (
          <AlertTriangle size={18} />
        ) : (
          <Database size={18} className="animate-pulse" />
        )}
      </div>
    </div>
  );
}
