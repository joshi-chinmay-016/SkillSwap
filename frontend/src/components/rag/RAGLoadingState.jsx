import React from "react";
import { Sparkles } from "lucide-react";

export default function RAGLoadingState() {
  return (
    <div className="bg-bg border border-border rounded-2xl p-6 shadow-xl space-y-4 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center text-accent">
          <Sparkles size={18} className="animate-spin" />
        </div>
        <span className="text-sm font-semibold text-text">Generating grounded answer...</span>
      </div>

      <div className="space-y-2 pt-2">
        <div className="h-4 bg-bg-alt rounded-md w-3/4" />
        <div className="h-4 bg-bg-alt rounded-md w-full" />
        <div className="h-4 bg-bg-alt rounded-md w-5/6" />
        <div className="h-4 bg-bg-alt rounded-md w-2/3" />
      </div>

      <div className="pt-4 flex gap-3">
        <div className="h-14 bg-bg-alt rounded-xl w-1/2" />
        <div className="h-14 bg-bg-alt rounded-xl w-1/2" />
      </div>
    </div>
  );
}
