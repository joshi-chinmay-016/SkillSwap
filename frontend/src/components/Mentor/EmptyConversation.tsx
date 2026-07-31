// src/components/Mentor/EmptyConversation.tsx

import React from "react";
import { Bot, Sparkles, BookOpen, Target, Compass } from "lucide-react";
import SuggestedPrompts from "./SuggestedPrompts";

interface EmptyConversationProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

export default function EmptyConversation({ onSelectPrompt, disabled }: EmptyConversationProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[380px] p-6 text-center max-w-lg mx-auto space-y-6">
      <div className="relative">
        <div className="w-16 h-16 rounded-2xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shadow-sm">
          <Bot className="w-8 h-8" />
        </div>
        <div className="absolute -bottom-1 -right-1 p-1 bg-accent text-white rounded-full shadow-xs">
          <Sparkles className="w-3.5 h-3.5" />
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-xl font-bold text-text tracking-tight">Hi! I'm your AI Learning Mentor</h3>
        <p className="text-xs text-text-secondary leading-relaxed">
          I adapt every explanation, code snippet, and topic recommendation to match your overall learning profile. Ask me anything to get started!
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full text-left">
        <div className="p-3 rounded-xl bg-bg border border-border space-y-1">
          <BookOpen className="w-4 h-4 text-accent" />
          <p className="font-semibold text-text text-xs">Custom Depth</p>
          <p className="text-[11px] text-text-secondary">Adapts to your level</p>
        </div>
        <div className="p-3 rounded-xl bg-bg border border-border space-y-1">
          <Target className="w-4 h-4 text-emerald-500" />
          <p className="font-semibold text-text text-xs">Gap Aware</p>
          <p className="text-[11px] text-text-secondary">Builds prerequisites</p>
        </div>
        <div className="p-3 rounded-xl bg-bg border border-border space-y-1">
          <Compass className="w-4 h-4 text-indigo-500" />
          <p className="font-semibold text-text text-xs">Next Steps</p>
          <p className="text-[11px] text-text-secondary">Guides your roadmap</p>
        </div>
      </div>

      <div className="w-full pt-2">
        <p className="text-xs font-medium text-text-secondary mb-3">Try one of these suggestions:</p>
        <SuggestedPrompts onSelectPrompt={onSelectPrompt} disabled={disabled} />
      </div>
    </div>
  );
}
