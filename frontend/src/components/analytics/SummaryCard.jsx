import React from "react";

export default function SummaryCard({
  title,
  value,
  icon: Icon,
  trend,
  trendDirection,
  subtext,
  className = "",
}) {
  const getTrendColor = () => {
    if (trendDirection === "up") return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    if (trendDirection === "down") return "text-rose-500 bg-rose-500/10 border-rose-500/20";
    return "text-slate-400 bg-slate-500/10 border-slate-500/20";
  };

  return (
    <div
      role="region"
      aria-label={title}
      className={`bg-card text-card-foreground border border-border rounded-xl p-5 shadow-xs transition-all hover:border-primary/30 flex flex-col justify-between ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
        {Icon && (
          <div className="p-2 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
            <Icon className="w-4 h-4" aria-hidden="true" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between gap-2">
        <div className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
          {value !== undefined && value !== null ? value : "—"}
        </div>
        {trend && (
          <span
            className={`inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full border ${getTrendColor()}`}
          >
            {trend}
          </span>
        )}
      </div>

      {subtext && (
        <p className="mt-2 text-xs text-muted-foreground truncate">
          {subtext}
        </p>
      )}
    </div>
  );
}
