// src/components/Mentor/ProfileSidebar.tsx

import React from "react";
import { UserCheck, Zap, AlertCircle, Compass, BookOpen, X, RefreshCw, Sparkles, Heart } from "lucide-react";
import type { AIContextResponse } from "../../types/aiContext";
import { useAIContext } from "../../hooks/useAIContext";

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
  const { regenerate, isRegenerating } = useAIContext();

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
        <div className="p-3.5 rounded-xl bg-bg-alt border border-border flex items-start gap-2.5 shadow-xs mb-3">
          <AlertCircle className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-text mb-1">Generic Mode Active</p>
            <p className="text-[11px] leading-relaxed">
              No persistent AI profile found yet. Complete a learning session to build your profile, or build it now based on your active journeys.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => regenerate()}
          disabled={isRegenerating}
          className="w-full py-2 px-3 rounded-lg bg-accent text-white font-semibold text-[11px] flex items-center justify-center gap-2 hover:bg-accent/90 disabled:opacity-50 transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? "animate-spin" : ""}`} />
          {isRegenerating ? "Building Profile..." : "Build AI Profile Now"}
        </button>
      </div>
    );
  }

  return (
    <div className="w-full lg:w-72 bg-bg border-l border-border p-4 space-y-4 overflow-y-auto shrink-0 text-xs h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-border">
        <div className="flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-accent" />
          <h2 className="font-bold text-text uppercase tracking-wider text-[11px]">AI Learner Profile</h2>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 bg-accent/10 text-accent font-semibold rounded-full text-[10px]" title={`Profile v${context.context_version}`}>
            v{context.context_version} • {context.completed_sessions} Sessions
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

      {/* Overall Progress Summary */}
      {context.overall_summary && (
        <div className="p-3 rounded-xl bg-accent/5 border border-accent/20">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-text">
              <Sparkles className="w-3.5 h-3.5 text-accent" />
              <span>Learner Summary</span>
            </div>
            <button
              type="button"
              onClick={() => regenerate()}
              disabled={isRegenerating}
              className="p-1 text-text-secondary hover:text-accent rounded-md hover:bg-bg-alt transition-colors cursor-pointer"
              title="Regenerate profile"
            >
              <RefreshCw className={`w-3 h-3 ${isRegenerating ? "animate-spin" : ""}`} />
            </button>
          </div>
          <p className="text-text-secondary leading-relaxed text-[11px]">
            {context.overall_summary}
          </p>
        </div>
      )}

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

      {/* Learning Interests */}
      {context.learning_interests && context.learning_interests.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 font-semibold text-text mb-2">
            <Heart className="w-3.5 h-3.5 text-rose-500" />
            <span>Learning Interests</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {context.learning_interests.map((interest, i) => (
              <span
                key={i}
                className="px-2 py-1 rounded-md bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 text-[11px] font-medium"
              >
                ♥ {interest}
              </span>
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

      {/* Manual Regenerate Button Footer */}
      <div className="pt-2 border-t border-border">
        <button
          type="button"
          onClick={() => regenerate()}
          disabled={isRegenerating}
          className="w-full py-1.5 px-3 rounded-lg border border-border bg-bg-alt hover:bg-accent/10 hover:border-accent/30 text-text-secondary hover:text-text font-medium text-[11px] flex items-center justify-center gap-2 transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3 h-3 ${isRegenerating ? "animate-spin text-accent" : ""}`} />
          {isRegenerating ? "Regenerating..." : "Sync & Refresh Profile"}
        </button>
      </div>
    </div>
  );
}
