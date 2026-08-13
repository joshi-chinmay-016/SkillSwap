import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function RAGErrorState({ error, onRetry }) {
  return (
    <div className="p-6 bg-danger/10 border border-danger/30 rounded-2xl space-y-4">
      <div className="flex items-center gap-3 text-danger font-bold text-sm">
        <AlertTriangle size={20} />
        <span>Something went wrong while generating the answer</span>
      </div>

      <p className="text-xs text-text-secondary leading-relaxed">
        We encountered an issue communicating with the RAG pipeline. Please verify your query or try again in a moment.
      </p>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-danger text-white text-xs font-semibold hover:bg-danger/90 transition-colors shadow-sm cursor-pointer"
        >
          <RefreshCw size={14} />
          <span>Try again</span>
        </button>
      )}
    </div>
  );
}
