// src/components/Mentor/MemoryCard.tsx

import React from "react";
import { Pin, Eye, Edit2, Archive, Trash2, Clock, CalendarCheck } from "lucide-react";
import type { MentorMemory } from "../../types/mentorMemory";
import MemoryBadge from "./MemoryBadge";

interface MemoryCardProps {
  memory: MentorMemory;
  onView: (memory: MentorMemory) => void;
  onEdit: (memory: MentorMemory) => void;
  onArchive: (memory: MentorMemory) => void;
  onForget: (memory: MentorMemory) => void;
  onTogglePin: (memory: MentorMemory) => void;
}

export default function MemoryCard({
  memory,
  onView,
  onEdit,
  onArchive,
  onForget,
  onTogglePin,
}: MemoryCardProps) {
  const isArchived = memory.status === "ARCHIVED";

  return (
    <div
      className={`group relative flex flex-col justify-between p-4 rounded-2xl border transition-all duration-200 ${
        memory.is_pinned
          ? "bg-gradient-to-br from-amber-500/5 via-bg to-bg border-amber-500/30 shadow-xs"
          : isArchived
          ? "bg-bg-alt/50 border-border/60 opacity-70"
          : "bg-bg border-border hover:border-accent/30 hover:shadow-sm"
      }`}
    >
      <div>
        {/* Top Header Row */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            <MemoryBadge type="category" value={memory.category} />
            <MemoryBadge type="importance" value={memory.importance} />
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => onTogglePin(memory)}
              className={`p-1.5 rounded-lg border transition-all cursor-pointer ${
                memory.is_pinned
                  ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 font-bold"
                  : "text-text-secondary border-transparent hover:bg-bg-alt hover:text-text"
              }`}
              title={memory.is_pinned ? "Unpin Memory" : "Pin Memory"}
            >
              <Pin className={`w-3.5 h-3.5 ${memory.is_pinned ? "fill-amber-500 text-amber-500" : ""}`} />
            </button>
          </div>
        </div>

        {/* Title */}
        <h3
          onClick={() => onView(memory)}
          className="text-sm font-bold text-text hover:text-accent cursor-pointer transition-colors line-clamp-1 mb-1"
        >
          {memory.title}
        </h3>

        {/* Content Description */}
        <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed mb-3">
          {memory.content}
        </p>
      </div>

      {/* Footer Info & Actions */}
      <div className="pt-2.5 border-t border-border/60 flex items-center justify-between gap-2 text-[11px] text-text-secondary">
        <div className="flex items-center gap-3">
          <MemoryBadge type="source" value={memory.source} />
          <span className="hidden sm:inline-flex items-center gap-1">
            <Clock className="w-3 h-3 text-text-secondary" />
            {new Date(memory.created_at).toLocaleDateString()}
          </span>
          {memory.last_used_at && (
            <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
              <CalendarCheck className="w-3 h-3" />
              Used Recently
            </span>
          )}
        </div>

        {/* Card Actions */}
        <div className="flex items-center gap-1 opacity-95 sm:opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={() => onView(memory)}
            className="p-1.5 rounded-lg hover:bg-accent/10 text-text-secondary hover:text-accent cursor-pointer"
            title="View Memory Details"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => onEdit(memory)}
            className="p-1.5 rounded-lg hover:bg-accent/10 text-text-secondary hover:text-accent cursor-pointer"
            title="Edit Memory"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          {!isArchived && (
            <button
              type="button"
              onClick={() => onArchive(memory)}
              className="p-1.5 rounded-lg hover:bg-amber-500/10 text-text-secondary hover:text-amber-500 cursor-pointer"
              title="Archive Memory"
            >
              <Archive className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={() => onForget(memory)}
            className="p-1.5 rounded-lg hover:bg-rose-500/10 text-text-secondary hover:text-rose-500 cursor-pointer"
            title="Forget Memory (Delete)"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
