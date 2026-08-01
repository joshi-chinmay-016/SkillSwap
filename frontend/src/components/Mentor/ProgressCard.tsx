// src/components/Mentor/ProgressCard.tsx

import React from "react";
import { BookOpen, Flame, Map, Award } from "lucide-react";

interface ProgressCardProps {
  data: {
    total_journeys?: number;
    completed_journeys?: number;
    completed_sessions?: number;
    completion_percentage?: number;
    current_streak?: number;
    longest_streak?: number;
    last_activity?: string | null;
  };
}

export default function ProgressCard({ data }: ProgressCardProps) {
  if (!data) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-2">
      {/* Completed Sessions */}
      <div className="p-2.5 rounded-xl bg-bg border border-border/80 flex flex-col justify-between space-y-1">
        <div className="flex items-center gap-1.5 text-accent">
          <BookOpen className="w-3.5 h-3.5" />
          <span className="text-[11px] font-medium text-text-secondary">Sessions</span>
        </div>
        <span className="text-base font-bold text-text tracking-tight">
          {data.completed_sessions ?? 0}
        </span>
      </div>

      {/* Current Streak */}
      <div className="p-2.5 rounded-xl bg-bg border border-border/80 flex flex-col justify-between space-y-1">
        <div className="flex items-center gap-1.5 text-amber-500">
          <Flame className="w-3.5 h-3.5" />
          <span className="text-[11px] font-medium text-text-secondary">Streak</span>
        </div>
        <span className="text-base font-bold text-text tracking-tight">
          {data.current_streak ?? 0} Days
        </span>
      </div>

      {/* Journeys */}
      <div className="p-2.5 rounded-xl bg-bg border border-border/80 flex flex-col justify-between space-y-1">
        <div className="flex items-center gap-1.5 text-indigo-500">
          <Map className="w-3.5 h-3.5" />
          <span className="text-[11px] font-medium text-text-secondary">Journeys</span>
        </div>
        <span className="text-base font-bold text-text tracking-tight">
          {data.total_journeys ?? 0}
        </span>
      </div>

      {/* Completion Rate */}
      <div className="p-2.5 rounded-xl bg-bg border border-border/80 flex flex-col justify-between space-y-1">
        <div className="flex items-center gap-1.5 text-emerald-500">
          <Award className="w-3.5 h-3.5" />
          <span className="text-[11px] font-medium text-text-secondary">Completion</span>
        </div>
        <span className="text-base font-bold text-text tracking-tight">
          {data.completion_percentage ?? 0}%
        </span>
      </div>
    </div>
  );
}
