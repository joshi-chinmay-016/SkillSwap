// src/components/Mentor/MemoryStatistics.tsx

import React from "react";
import { Brain, Pin, Star, CalendarCheck, BarChart3, Clock } from "lucide-react";
import type { MentorMemoryStats } from "../../types/mentorMemory";

interface MemoryStatisticsProps {
  stats?: MentorMemoryStats | null;
  isLoading?: boolean;
}

export default function MemoryStatistics({ stats, isLoading }: MemoryStatisticsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-4 rounded-2xl border border-border bg-bg animate-pulse h-24" />
        ))}
      </div>
    );
  }

  const total = stats?.total_memories ?? 0;
  const pinned = stats?.pinned_count ?? 0;
  const highImp = stats?.high_importance_count ?? 0;
  const recentlyUsed = stats?.recently_used_count ?? 0;

  const statCards = [
    {
      title: "Total Memories",
      value: total,
      icon: Brain,
      color: "text-accent bg-accent/10 border-accent/20",
    },
    {
      title: "Pinned",
      value: pinned,
      icon: Pin,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    },
    {
      title: "High Importance",
      value: highImp,
      icon: Star,
      color: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
    },
    {
      title: "Recently Used",
      value: recentlyUsed,
      icon: CalendarCheck,
      color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    },
  ];

  return (
    <div className="space-y-4 mb-6">
      {/* Top 4 Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.title}
              className="p-4 rounded-2xl border border-border bg-bg flex items-center justify-between gap-3 shadow-xs hover:border-accent/30 transition-all"
            >
              <div>
                <p className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
                  {card.title}
                </p>
                <p className="text-xl font-extrabold text-text mt-0.5">{card.value}</p>
              </div>
              <div className={`p-2.5 rounded-xl border ${card.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail Breakdown Panel */}
      {stats && (stats.most_used_category || stats.oldest_memory_date) && (
        <div className="p-4 rounded-2xl border border-border bg-bg/50 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-accent" />
            <span className="text-text-secondary">Most Used Category:</span>
            <span className="font-bold text-text bg-bg px-2 py-0.5 rounded-md border border-border">
              {stats.most_used_category || "N/A"}
            </span>
          </div>

          <div className="flex items-center gap-4 text-text-secondary">
            {stats.oldest_memory_date && (
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                Oldest: {new Date(stats.oldest_memory_date).toLocaleDateString()}
              </span>
            )}
            {stats.newest_memory_date && (
              <span className="flex items-center gap-1 font-medium text-text">
                Newest: {new Date(stats.newest_memory_date).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
