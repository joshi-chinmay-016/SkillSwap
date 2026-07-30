// src/components/Mentor/MentorHeader.tsx

import React from "react";
import { Bot, Sparkles, RefreshCw, Layers } from "lucide-react";

interface MentorHeaderProps {
  onClear: () => void;
  hasMessages: boolean;
  contextVersion?: number;
}

export default function MentorHeader({ onClear, hasMessages, contextVersion = 1 }: MentorHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-bg border-b border-border shrink-0">
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shadow-xs">
            <Bot className="w-5 h-5" />
          </div>
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
          </span>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-text tracking-tight">AI Learning Mentor</h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-accent/10 text-accent border border-accent/15">
              <Sparkles className="w-3 h-3" /> Context-Aware
            </span>
          </div>
          <p className="text-xs text-text-secondary">
            Personalized guidance powered by your long-term learning profile
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-bg-alt border border-border text-[11px] text-text-secondary">
          <Layers className="w-3.5 h-3.5 text-accent" />
          <span>Profile v{contextVersion}</span>
        </div>

        {hasMessages && (
          <button
            type="button"
            onClick={onClear}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-text-secondary hover:text-text hover:bg-bg-alt text-xs font-medium transition-colors cursor-pointer"
            title="Clear current session messages"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Chat</span>
          </button>
        )}
      </div>
    </div>
  );
}
