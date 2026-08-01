// src/components/Mentor/AnalyticsCard.tsx

import React from "react";
import { TrendingUp, Calendar, Zap, Activity } from "lucide-react";

interface AnalyticsCardProps {
  data: {
    weekly_activity?: Record<string, number>;
    learning_trend?: { direction?: string; percentage?: number } | null;
    learning_velocity?: number;
    most_active_day?: { day?: string; count?: number } | null;
    average_per_day?: number;
    current_streak?: number;
    longest_streak?: number;
    consistency_score?: number;
  };
}

export default function AnalyticsCard({ data }: AnalyticsCardProps) {
  if (!data) return null;

  const trendDir = data.learning_trend?.direction || "stable";
  const trendPct = data.learning_trend?.percentage ?? 0;

  return (
    <div className="space-y-2.5 my-2">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Trend */}
        <div className="p-2.5 rounded-xl bg-bg border border-border/80 space-y-1">
          <div className="flex items-center gap-1.5 text-indigo-500">
            <TrendingUp className="w-3.5 h-3.5" />
            <span className="text-[11px] font-medium text-text-secondary">Trend</span>
          </div>
          <p className="text-xs font-bold text-text capitalize">
            {trendDir} {trendPct > 0 ? `(${trendPct}%)` : ""}
          </p>
        </div>

        {/* Velocity */}
        <div className="p-2.5 rounded-xl bg-bg border border-border/80 space-y-1">
          <div className="flex items-center gap-1.5 text-emerald-500">
            <Zap className="w-3.5 h-3.5" />
            <span className="text-[11px] font-medium text-text-secondary">Velocity</span>
          </div>
          <p className="text-xs font-bold text-text">
            {data.learning_velocity ?? 0} hrs/wk
          </p>
        </div>

        {/* Most Active Day */}
        <div className="p-2.5 rounded-xl bg-bg border border-border/80 space-y-1">
          <div className="flex items-center gap-1.5 text-amber-500">
            <Calendar className="w-3.5 h-3.5" />
            <span className="text-[11px] font-medium text-text-secondary">Peak Day</span>
          </div>
          <p className="text-xs font-bold text-text">
            {data.most_active_day?.day || "N/A"}
          </p>
        </div>

        {/* Consistency */}
        <div className="p-2.5 rounded-xl bg-bg border border-border/80 space-y-1">
          <div className="flex items-center gap-1.5 text-accent">
            <Activity className="w-3.5 h-3.5" />
            <span className="text-[11px] font-medium text-text-secondary">Consistency</span>
          </div>
          <p className="text-xs font-bold text-text">
            {data.consistency_score ? `${Math.round(data.consistency_score * 100)}%` : "N/A"}
          </p>
        </div>
      </div>
    </div>
  );
}
