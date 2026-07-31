// src/components/Mentor/SuggestedPrompts.tsx

import React from "react";
import { Sparkles, HelpCircle, Code, Lightbulb, Compass } from "lucide-react";

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

const DEFAULT_SUGGESTIONS = [
  { label: "Explain Graphs", icon: Compass, prompt: "Explain Graph Data Structures and Graph Traversal algorithms step by step." },
  { label: "Review Binary Search", icon: Code, prompt: "Review Binary Search algorithm, edge cases, and time complexity." },
  { label: "Help with DP", icon: Lightbulb, prompt: "Help me understand Dynamic Programming principles and memoization." },
  { label: "Suggest Next Topic", icon: Sparkles, prompt: "Based on my learning profile, what topic should I learn next and why?" },
];

export default function SuggestedPrompts({ onSelectPrompt, disabled }: SuggestedPromptsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {DEFAULT_SUGGESTIONS.map((item, i) => {
        const Icon = item.icon;
        return (
          <button
            key={i}
            type="button"
            disabled={disabled}
            onClick={() => onSelectPrompt(item.prompt)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-bg border border-border text-xs text-text-secondary hover:text-accent hover:border-accent/40 hover:bg-accent/5 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Icon className="w-3.5 h-3.5 text-accent" />
            <span>{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
