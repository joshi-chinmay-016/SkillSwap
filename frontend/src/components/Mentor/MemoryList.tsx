// src/components/Mentor/MemoryList.tsx

import React, { useState } from "react";
import { LayoutGrid, ListFilter, Clock, Plus } from "lucide-react";
import type { MentorMemory } from "../../types/mentorMemory";
import MemoryCard from "./MemoryCard";
import MemoryTimeline from "./MemoryTimeline";
import EmptyMemoryState from "./EmptyMemoryState";

interface MemoryListProps {
  memories: MentorMemory[];
  isLoading?: boolean;
  onView: (memory: MentorMemory) => void;
  onEdit: (memory: MentorMemory) => void;
  onArchive: (memory: MentorMemory) => void;
  onForget: (memory: MentorMemory) => void;
  onTogglePin: (memory: MentorMemory) => void;
  onAddManual?: () => void;
  isSearchOrFilterActive?: boolean;
  onClearFilters?: () => void;
}

export default function MemoryList({
  memories,
  isLoading = false,
  onView,
  onEdit,
  onArchive,
  onForget,
  onTogglePin,
  onAddManual,
  isSearchOrFilterActive = false,
  onClearFilters,
}: MemoryListProps) {
  const [viewMode, setViewMode] = useState<"cards" | "timeline">("cards");

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-4 rounded-2xl border border-border bg-bg animate-pulse h-40" />
        ))}
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <EmptyMemoryState
        onAddManual={onAddManual}
        isSearchOrFilterActive={isSearchOrFilterActive}
        onClearFilters={onClearFilters}
      />
    );
  }

  // PART 3 Order: Pinned ↓ High Importance ↓ Recently Used
  const sortedMemories = [...memories].sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) {
      return a.is_pinned ? -1 : 1;
    }

    const impWeight: Record<string, number> = {
      CRITICAL: 4,
      HIGH: 3,
      MEDIUM: 2,
      LOW: 1,
    };
    const impA = impWeight[a.importance.toUpperCase()] || 0;
    const impB = impWeight[b.importance.toUpperCase()] || 0;

    if (impA !== impB) {
      return impB - impA;
    }

    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className="space-y-4">
      {/* Top View Toggle Toolbar */}
      <div className="flex items-center justify-between gap-3 pt-1">
        <p className="text-xs font-semibold text-text-secondary">
          Showing <span className="text-text font-bold">{sortedMemories.length}</span> memories
        </p>

        <div className="flex items-center gap-2">
          {onAddManual && (
            <button
              type="button"
              onClick={onAddManual}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-accent/10 border border-accent/20 text-accent hover:bg-accent hover:text-white transition-all text-xs font-bold cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Memory</span>
            </button>
          )}

          <div className="inline-flex p-0.5 rounded-xl bg-bg border border-border text-xs">
            <button
              type="button"
              onClick={() => setViewMode("cards")}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                viewMode === "cards"
                  ? "bg-accent text-white shadow-xs"
                  : "text-text-secondary hover:text-text"
              }`}
              title="Cards View"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Cards</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("timeline")}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                viewMode === "timeline"
                  ? "bg-accent text-white shadow-xs"
                  : "text-text-secondary hover:text-text"
              }`}
              title="Timeline View"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Timeline</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content Rendering */}
      {viewMode === "cards" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sortedMemories.map((memory) => (
            <MemoryCard
              key={memory.id}
              memory={memory}
              onView={onView}
              onEdit={onEdit}
              onArchive={onArchive}
              onForget={onForget}
              onTogglePin={onTogglePin}
            />
          ))}
        </div>
      ) : (
        <MemoryTimeline memories={sortedMemories} onView={onView} />
      )}
    </div>
  );
}
