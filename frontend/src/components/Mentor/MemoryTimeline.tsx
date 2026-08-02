// src/components/Mentor/MemoryTimeline.tsx

import React from "react";
import { Clock, Pin } from "lucide-react";
import type { MentorMemory } from "../../types/mentorMemory";
import MemoryBadge from "./MemoryBadge";

interface MemoryTimelineProps {
  memories: MentorMemory[];
  onView: (memory: MentorMemory) => void;
}

export default function MemoryTimeline({ memories, onView }: MemoryTimelineProps) {
  // Sort chronologically (newest first)
  const sorted = [...memories].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
      {sorted.map((memory) => (
        <div key={memory.id} className="relative group">
          {/* Node marker */}
          <div className="absolute -left-[27px] top-1.5 w-3.5 h-3.5 rounded-full border-2 border-bg bg-accent shadow-xs group-hover:scale-125 transition-transform" />

          <div
            onClick={() => onView(memory)}
            className="p-4 rounded-xl border border-border bg-bg hover:border-accent/30 hover:shadow-xs transition-all cursor-pointer"
          >
            <div className="flex items-center justify-between gap-2 mb-1">
              <div className="flex items-center gap-2">
                <MemoryBadge type="category" value={memory.category} />
                {memory.is_pinned && (
                  <span className="inline-flex items-center gap-1 text-xs text-amber-500 font-semibold">
                    <Pin className="w-3 h-3 fill-amber-500" /> Pinned
                  </span>
                )}
              </div>
              <span className="text-[11px] text-text-secondary flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(memory.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            </div>

            <h4 className="text-sm font-bold text-text group-hover:text-accent transition-colors">
              {memory.title}
            </h4>
            <p className="text-xs text-text-secondary mt-1 line-clamp-2">{memory.content}</p>

            <div className="mt-2 pt-2 border-t border-border/50 flex items-center gap-2">
              <MemoryBadge type="importance" value={memory.importance} />
              <MemoryBadge type="source" value={memory.source} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
