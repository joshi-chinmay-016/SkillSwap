import React from "react";

export function MarkerHighlight({
  children,
  color = "yellow", // 'yellow', 'cyan', 'pink', 'emerald'
  className = "",
}) {
  const colorClass = {
    yellow: "highlight-marker-yellow text-slate-900 dark:text-slate-900 font-bold",
    cyan: "highlight-marker-cyan text-slate-900 dark:text-slate-900 font-bold",
    pink: "highlight-marker-pink text-slate-900 dark:text-slate-900 font-bold",
    emerald: "highlight-marker-emerald text-slate-900 dark:text-slate-900 font-bold",
  }[color] || "highlight-marker-yellow";

  return <span className={`inline-block ${colorClass} ${className}`}>{children}</span>;
}

export function HandDrawnNote({
  children,
  color = "rose", // 'rose', 'cyan', 'amber', 'purple'
  rotate = "-3deg",
  className = "",
}) {
  const textColor = {
    rose: "text-rose-600 dark:text-rose-400",
    cyan: "text-sky-600 dark:text-sky-400",
    amber: "text-amber-600 dark:text-amber-400",
    purple: "text-purple-600 dark:text-purple-400",
    emerald: "text-emerald-600 dark:text-emerald-400",
  }[color] || "text-rose-600 dark:text-rose-400";

  return (
    <span
      style={{ transform: `rotate(${rotate})` }}
      className={`inline-block font-handwriting text-xl sm:text-2xl font-bold tracking-wide select-none ${textColor} ${className}`}
    >
      {children}
    </span>
  );
}

export function SquigglyUnderline({ className = "text-rose-500" }) {
  return (
    <svg
      className={`w-full h-3 -mt-1 overflow-visible ${className}`}
      viewBox="0 0 100 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="none"
    >
      <path
        d="M2 7.5C12 3.5 22 10.5 32 6.5C42 2.5 52 9.5 62 6C72 2.5 82 8.5 98 4.5"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
