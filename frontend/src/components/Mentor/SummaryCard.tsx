// src/components/Mentor/SummaryCard.tsx

import React from "react";
import { BookMarked, CheckSquare, Sparkles, AlertCircle } from "lucide-react";

interface SummaryCardProps {
  data: {
    has_summary?: boolean;
    session_title?: string;
    summary?: string;
    key_takeaways?: string[];
    strengths?: string[];
    weaknesses?: string[];
    follow_up_topics?: string[];
    message?: string;
  };
}

export default function SummaryCard({ data }: SummaryCardProps) {
  if (!data) return null;

  if (!data.has_summary) {
    return (
      <div className="p-3 rounded-xl bg-bg border border-border/80 text-xs text-text-secondary my-2">
        <p className="font-medium text-text">{data.session_title || "Latest Session"}</p>
        <p className="text-[11px] mt-1">{data.message || "No session summary recorded yet."}</p>
      </div>
    );
  }

  return (
    <div className="p-3 rounded-xl bg-bg border border-border/80 space-y-2.5 my-2 text-xs">
      {/* Session Title & Summary Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-1.5 text-accent font-bold">
          <BookMarked className="w-3.5 h-3.5" />
          <span>Latest Session: {data.session_title}</span>
        </div>
        {data.summary && (
          <p className="text-[11px] text-text-secondary leading-relaxed pl-5">
            {data.summary}
          </p>
        )}
      </div>

      {/* Key Takeaways */}
      {data.key_takeaways && data.key_takeaways.length > 0 && (
        <div className="space-y-1 pt-1.5 border-t border-border/60">
          <p className="font-semibold text-text text-[11px] flex items-center gap-1">
            <CheckSquare className="w-3.5 h-3.5 text-emerald-500" />
            Key Takeaways
          </p>
          <ul className="space-y-0.5 pl-5 list-disc text-[11px] text-text-secondary">
            {data.key_takeaways.slice(0, 3).map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Follow-up Topics */}
      {data.follow_up_topics && data.follow_up_topics.length > 0 && (
        <div className="pt-1.5 border-t border-border/60 flex items-center gap-1.5 flex-wrap">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
          <span className="text-[11px] font-medium text-text-secondary">Next:</span>
          {data.follow_up_topics.slice(0, 3).map((topic, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 text-[10px] font-medium"
            >
              {topic}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
