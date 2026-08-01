// src/components/Mentor/JourneyCard.tsx

import React from "react";
import { Compass, CheckCircle2, ArrowRight } from "lucide-react";

interface JourneyCardProps {
  data: {
    total_journeys?: number;
    completed_journeys?: number;
    current_journey?: {
      id?: number;
      title?: string;
      target_role?: string;
      progress_percentage?: number;
      current_week?: number;
      total_weeks?: number;
    } | null;
    next_milestone?: {
      week_number?: number;
      topic?: string;
      goal?: string;
      status?: string;
    } | null;
  };
}

export default function JourneyCard({ data }: JourneyCardProps) {
  if (!data) return null;

  const current = data.current_journey;
  const nextMilestone = data.next_milestone;

  return (
    <div className="p-3 rounded-xl bg-bg border border-border/80 space-y-2.5 my-2">
      {current ? (
        <div>
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-accent shrink-0" />
              <span className="text-xs font-bold text-text">{current.title}</span>
            </div>
            <span className="text-[11px] font-semibold text-accent">
              {current.progress_percentage ?? 0}%
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-1.5 bg-accent/10 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-accent transition-all duration-300 rounded-full"
              style={{ width: `${Math.min(100, Math.max(0, current.progress_percentage || 0))}%` }}
            />
          </div>

          {/* Week & Role */}
          <div className="flex items-center justify-between text-[11px] text-text-secondary">
            <span>Role: {current.target_role || "Software Engineer"}</span>
            <span>
              Week {current.current_week || 1} of {current.total_weeks || 12}
            </span>
          </div>
        </div>
      ) : (
        <p className="text-xs text-text-secondary">
          No active journey found. Start a roadmap to track your learning journey!
        </p>
      )}

      {/* Next Milestone */}
      {nextMilestone && (
        <div className="pt-2 border-t border-border/60 flex items-start gap-2 text-xs">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-text text-[11px]">
              Next Milestone: Week {nextMilestone.week_number} — {nextMilestone.topic}
            </p>
            {nextMilestone.goal && (
              <p className="text-[10px] text-text-secondary line-clamp-1">{nextMilestone.goal}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
