import React from "react";
import { Sparkles, BarChart2, BookOpen, Map, UserCheck, Wrench } from "lucide-react";

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

const DEFAULT_SUGGESTIONS = [
  { label: "Show my progress", icon: BarChart2, prompt: "How many sessions have I completed and what is my current streak?" },
  { label: "Summarize my last session", icon: BookOpen, prompt: "Summarize my last learning session and key takeaways." },
  { label: "Analyze my learning", icon: Wrench, prompt: "Show my learning analytics, trends, and statistics." },
  { label: "My active journey", icon: Map, prompt: "What is my current roadmap and next milestone in my learning journey?" },
  { label: "Review my strengths", icon: UserCheck, prompt: "Show my strong topics and weak topics from my learning profile." },
  { label: "What to learn next?", icon: Sparkles, prompt: "Based on my learning profile, what topic should I learn next?" },
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
