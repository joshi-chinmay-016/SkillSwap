// src/components/Mentor/ProfileSidebar.tsx

import React from "react";
import { UserCheck, Zap, AlertCircle, Compass, BookOpen, X } from "lucide-react";
import type { AIContextResponse } from "../../types/aiContext";

interface ProfileSidebarProps {
  context: AIContextResponse | null;
  isLoading: boolean;
  onTopicClick?: (topic: string) => void;
  onClose?: () => void;
}

export default function ProfileSidebar({
  context,
  isLoading,
  onTopicClick,
  onClose,
}: ProfileSidebarProps) {
  if (isLoading) {
    return (
      <div className="w-full lg:w-72 bg-bg border-l border-border p-4 space-y-4 animate-pulse shrink-0">
        <div className="h-5 bg-bg-alt rounded w-2/3" />
        <div className="h-20 bg-bg-alt rounded-lg" />
        <div className="h-16 bg-bg-alt rounded-lg" />
        <div className="h-16 bg-bg-alt rounded-lg" />
      </div>
    );
  }

  if (!context) {
    return (
      <div className="w-full lg:w-72 bg-bg border-l border-border p-4 shrink-0 text-xs text-text-secondary">
        <div className="flex items-center justify-between pb-2 border-b border-border mb-3">
          <span className="font-bold text-text uppercase tracking-wider text-[11px]">AI Profile Status</span>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer"
              title="Close panel"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <div className="p-3.5 rounded-xl bg-bg-alt border border-border flex items-start gap-2.5 shadow-xs">
          <AlertCircle className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-text mb-1">Generic Mode Active</p>
            <p className="text-[11px] leading-relaxed">
              No persistent AI profile found yet. Complete a learning session to unlock customized guidance.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full lg:w-72 bg-bg border-l border-border p-4 space-y-4 overflow-y-auto shrink-0 text-xs h-full">
      <div className="flex items-center justify-between pb-2 border-b border-border">
        <div className="flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-accent" />
          <h2 className="font-bold text-text uppercase tracking-wider text-[11px]">AI Learner Profile</h2>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 bg-accent/10 text-accent font-semibold rounded-full text-[10px]">
            {context.completed_sessions} Sessions
          </span>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer"
              title="Close profile panel"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Learning Style */}
      {context.learning_style && (
        <div className="p-3 rounded-lg bg-bg-alt border border-border">
          <div className="flex items-center gap-1.5 font-semibold text-text mb-1.5">
            <BookOpen className="w-3.5 h-3.5 text-accent" />
            <span>Learning Style</span>
          </div>
          <p className="text-text-secondary leading-relaxed text-[11px]">
            {context.learning_style}
          </p>
        </div>
      )}

      {/* Strong Topics */}
      {context.strong_topics && context.strong_topics.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 font-semibold text-text mb-2">
            <Zap className="w-3.5 h-3.5 text-emerald-500" />
            <span>Mastered Topics</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {context.strong_topics.map((topic, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onTopicClick?.(`Ask me something advanced about ${topic}`)}
                className="px-2 py-1 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-[11px] font-medium hover:bg-emerald-500/20 transition-colors cursor-pointer"
              >
                ✓ {topic}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Weak Topics */}
      {context.weak_topics && context.weak_topics.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 font-semibold text-text mb-2">
            <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
            <span>Knowledge Gaps</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {context.weak_topics.map((topic, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onTopicClick?.(`Explain ${topic} step by step with code`)}
                className="px-2 py-1 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 text-[11px] font-medium hover:bg-amber-500/20 transition-colors cursor-pointer"
              >
                ⚠ {topic}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Topics */}
      {context.recommended_topics && context.recommended_topics.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 font-semibold text-text mb-2">
            <Compass className="w-3.5 h-3.5 text-indigo-500" />
            <span>Recommended Next</span>
          </div>
          <div className="space-y-1.5">
            {context.recommended_topics.slice(0, 4).map((topic, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onTopicClick?.(`Help me learn ${topic}`)}
                className="w-full text-left p-2 rounded-lg bg-bg-alt hover:bg-accent/10 hover:border-accent/30 border border-border text-text transition-colors flex items-center justify-between group cursor-pointer"
              >
                <span className="truncate">{topic}</span>
                <span className="text-[10px] text-text-secondary group-hover:text-accent font-medium">Ask →</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
