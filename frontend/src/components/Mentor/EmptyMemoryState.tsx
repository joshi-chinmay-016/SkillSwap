// src/components/Mentor/EmptyMemoryState.tsx

import React from "react";
import { Brain, Sparkles, Plus } from "lucide-react";

interface EmptyMemoryStateProps {
  onAddManual?: () => void;
  isSearchOrFilterActive?: boolean;
  onClearFilters?: () => void;
}

export default function EmptyMemoryState({
  onAddManual,
  isSearchOrFilterActive,
  onClearFilters,
}: EmptyMemoryStateProps) {
  if (isSearchOrFilterActive) {
    return (
      <div className="p-12 text-center border-2 border-dashed border-border rounded-3xl bg-bg/50 my-6">
        <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center mx-auto mb-3">
          <Brain className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-text">No matching memories found</h3>
        <p className="text-xs text-text-secondary mt-1 max-w-sm mx-auto">
          Try adjusting your search criteria or selecting a different category filter.
        </p>
        {onClearFilters && (
          <button
            type="button"
            onClick={onClearFilters}
            className="mt-4 px-4 py-2 rounded-xl bg-bg border border-border text-xs font-semibold text-text hover:bg-bg-alt transition-colors cursor-pointer"
          >
            Clear Filters
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="p-12 text-center border-2 border-dashed border-border rounded-3xl bg-bg my-6 max-w-lg mx-auto">
      <div className="relative w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center mx-auto mb-4">
        <Brain className="w-7 h-7" />
        <Sparkles className="w-4 h-4 text-amber-500 absolute -top-1 -right-1" />
      </div>
      <h3 className="text-lg font-bold text-text">AI Memory</h3>
      <p className="text-xs text-text-secondary mt-2 leading-relaxed">
        Your mentor hasn't stored any long-term memories yet.
        <br />
        As you continue learning, important preferences, goals, and learning styles will appear here.
      </p>
      {onAddManual && (
        <button
          type="button"
          onClick={onAddManual}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-accent text-white font-bold text-xs shadow-md hover:bg-accent/90 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Add Memory Manually
        </button>
      )}
    </div>
  );
}
