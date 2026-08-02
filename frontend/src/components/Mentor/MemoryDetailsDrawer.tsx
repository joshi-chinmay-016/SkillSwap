// src/components/Mentor/MemoryDetailsDrawer.tsx

import React from "react";
import { X, HelpCircle, Calendar, Clock, Pin, Edit2, Archive, Trash2 } from "lucide-react";
import type { MentorMemory } from "../../types/mentorMemory";
import MemoryBadge from "./MemoryBadge";

interface MemoryDetailsDrawerProps {
  memory: MentorMemory | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (memory: MentorMemory) => void;
  onArchive?: (memory: MentorMemory) => void;
  onForget?: (memory: MentorMemory) => void;
  onTogglePin?: (memory: MentorMemory) => void;
}

export default function MemoryDetailsDrawer({
  memory,
  isOpen,
  onClose,
  onEdit,
  onArchive,
  onForget,
  onTogglePin,
}: MemoryDetailsDrawerProps) {
  if (!isOpen || !memory) return null;

  const defaultWhyText =
    memory.why_remembered ||
    `The AI Mentor identified this as a durable preference or fact from your learning sessions and interactions (${memory.source}).`;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <aside className="fixed right-0 top-0 bottom-0 w-full sm:w-96 bg-bg border-l border-border z-50 flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MemoryBadge type="category" value={memory.category} />
            {memory.is_pinned && (
              <span className="inline-flex items-center gap-1 text-xs text-amber-500 font-bold">
                <Pin className="w-3 h-3 fill-amber-500" /> Pinned
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text hover:bg-bg-alt transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Title */}
          <div>
            <h2 className="text-base font-bold text-text leading-snug">{memory.title}</h2>
            <p className="text-xs text-text-secondary mt-2 leading-relaxed whitespace-pre-wrap">
              {memory.content}
            </p>
          </div>

          <div className="h-px bg-border" />

          {/* Attributes Grid */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <p className="text-text-secondary font-medium">Importance</p>
              <div className="mt-1">
                <MemoryBadge type="importance" value={memory.importance} />
              </div>
            </div>

            <div>
              <p className="text-text-secondary font-medium">Source</p>
              <div className="mt-1">
                <MemoryBadge type="source" value={memory.source} />
              </div>
            </div>

            <div>
              <p className="text-text-secondary font-medium flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Created
              </p>
              <p className="font-semibold text-text mt-1">
                {new Date(memory.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </p>
            </div>

            <div>
              <p className="text-text-secondary font-medium flex items-center gap-1">
                <Clock className="w-3 h-3" /> Last Used
              </p>
              <p className="font-semibold text-text mt-1">
                {memory.last_used_at
                  ? new Date(memory.last_used_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })
                  : "Not used yet"}
              </p>
            </div>
          </div>

          <div className="h-px bg-border" />

          {/* PART 8 — "Why was this remembered?" Section */}
          <div className="p-4 rounded-2xl bg-accent/5 border border-accent/15 space-y-2">
            <div className="flex items-center gap-2 text-accent font-bold text-xs">
              <HelpCircle className="w-4 h-4" />
              <span>Why this memory exists</span>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">{defaultWhyText}</p>
          </div>
        </div>

        {/* Footer Quick Actions */}
        <div className="p-4 border-t border-border bg-bg-alt/50 flex items-center justify-between gap-2">
          {onTogglePin && (
            <button
              type="button"
              onClick={() => onTogglePin(memory)}
              className="flex-1 py-2 px-3 rounded-xl border border-border bg-bg text-xs font-semibold text-text hover:bg-bg-alt transition-colors cursor-pointer flex items-center justify-center gap-1.5"
            >
              <Pin className={`w-3.5 h-3.5 ${memory.is_pinned ? "fill-amber-500 text-amber-500" : ""}`} />
              {memory.is_pinned ? "Unpin" : "Pin"}
            </button>
          )}

          {onEdit && (
            <button
              type="button"
              onClick={() => onEdit(memory)}
              className="flex-1 py-2 px-3 rounded-xl border border-border bg-bg text-xs font-semibold text-text hover:bg-bg-alt transition-colors cursor-pointer flex items-center justify-center gap-1.5"
            >
              <Edit2 className="w-3.5 h-3.5 text-accent" />
              Edit
            </button>
          )}

          {onArchive && memory.status !== "ARCHIVED" && (
            <button
              type="button"
              onClick={() => onArchive(memory)}
              className="py-2 px-3 rounded-xl border border-border bg-bg text-xs font-semibold text-amber-500 hover:bg-amber-500/10 transition-colors cursor-pointer"
              title="Archive Memory"
            >
              <Archive className="w-3.5 h-3.5" />
            </button>
          )}

          {onForget && (
            <button
              type="button"
              onClick={() => onForget(memory)}
              className="py-2 px-3 rounded-xl border border-border bg-bg text-xs font-semibold text-rose-500 hover:bg-rose-500/10 transition-colors cursor-pointer"
              title="Forget Memory"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
