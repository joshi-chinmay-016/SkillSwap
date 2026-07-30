// src/components/Mentor/TypingIndicator.tsx

import React from "react";
import { Bot } from "lucide-react";

export default function TypingIndicator() {
  return (
    <div className="flex gap-3 justify-start items-start animate-fade-in">
      <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shadow-xs">
        <Bot className="w-4 h-4" />
      </div>
      <div className="bg-bg border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-xs">
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-secondary font-medium">AI Mentor is thinking</span>
          <div className="flex gap-1 items-center">
            <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
