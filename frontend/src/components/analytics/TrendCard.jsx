import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export default function TrendCard({ trendInfo }) {
  const { percentage = 0, direction = "stable" } = trendInfo || {};

  const getTrendConfig = () => {
    if (direction === "up") {
      return {
        icon: TrendingUp,
        color: "text-emerald-500",
        bg: "bg-emerald-500/10 border-emerald-500/20",
        label: `↑ +${Math.abs(percentage)}%`,
        description: "Compared to last week",
      };
    }
    if (direction === "down") {
      return {
        icon: TrendingDown,
        color: "text-rose-500",
        bg: "bg-rose-500/10 border-rose-500/20",
        label: `↓ -${Math.abs(percentage)}%`,
        description: "Compared to last week",
      };
    }
    return {
      icon: Minus,
      color: "text-slate-400",
      bg: "bg-slate-500/10 border-slate-500/20",
      label: "↔ 0%",
      description: "Consistent with last week",
    };
  };

  const config = getTrendConfig();
  const IconComponent = config.icon;

  return (
    <div
      role="region"
      aria-label="Learning Trend"
      className="bg-card border border-border rounded-xl p-5 shadow-xs flex flex-col justify-between"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Learning Trend
        </span>
        <div className={`p-2 rounded-lg border ${config.bg} ${config.color}`}>
          <IconComponent className="w-4 h-4" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-1">
        <div className={`text-2xl font-extrabold tracking-tight ${config.color}`}>
          {config.label}
        </div>
        <p className="text-xs text-muted-foreground">{config.description}</p>
      </div>
    </div>
  );
}
