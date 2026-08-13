import React, { useState } from "react";
import { Sparkles, Send, RotateCcw, SlidersHorizontal } from "lucide-react";

export default function RAGInput({
  onSubmit,
  isPending,
  onReset,
  hasAnswer,
  responseStyle,
  setResponseStyle,
}) {
  const [query, setQuery] = useState("");
  const [showOptions, setShowOptions] = useState(false);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || isPending) return;
    onSubmit(query.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClear = () => {
    setQuery("");
    if (onReset) onReset();
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-3" aria-label="RAG Query Form">
      <div className="relative rounded-2xl bg-bg-alt/80 border border-border p-2 shadow-lg focus-within:ring-2 focus-within:ring-accent focus-within:border-transparent transition-all">
        <textarea
          id="rag-query-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your knowledge base anything... (Press Enter to submit)"
          rows={3}
          disabled={isPending}
          className="w-full bg-transparent px-4 py-2.5 text-sm text-text placeholder-text-secondary focus:outline-none resize-none disabled:opacity-50 font-sans"
          aria-label="Question to knowledge base"
        />

        <div className="flex items-center justify-between px-3 py-1.5 border-t border-border/50">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowOptions(!showOptions)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium text-text-secondary hover:text-text hover:bg-bg/60 transition-colors cursor-pointer"
              title="Toggle generation settings"
            >
              <SlidersHorizontal size={13} />
              <span className="capitalize">Style: {responseStyle}</span>
            </button>

            {hasAnswer && (
              <button
                type="button"
                onClick={handleClear}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium text-text-secondary hover:text-danger hover:bg-danger/10 transition-colors cursor-pointer"
                title="Reset question & answer"
              >
                <RotateCcw size={12} />
                <span>Reset</span>
              </button>
            )}
          </div>

          <button
            type="submit"
            disabled={!query.trim() || isPending}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-accent text-white font-medium text-xs hover:bg-accent-hover active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md cursor-pointer"
          >
            {isPending ? (
              <>
                <Sparkles size={14} className="animate-spin" />
                <span>Thinking...</span>
              </>
            ) : (
              <>
                <Send size={14} />
                <span>Ask RAG</span>
              </>
            )}
          </button>
        </div>
      </div>

      {showOptions && (
        <div className="p-3 bg-bg-alt/50 border border-border rounded-xl flex items-center justify-between text-xs animate-fadeIn">
          <span className="text-text-secondary font-medium">Answer Response Style:</span>
          <div className="flex items-center gap-1.5">
            {["concise", "detailed", "explanatory"].map((style) => (
              <button
                key={style}
                type="button"
                onClick={() => setResponseStyle(style)}
                className={`px-3 py-1 rounded-lg font-semibold capitalize transition-all cursor-pointer ${
                  responseStyle === style
                    ? "bg-accent text-white shadow-sm"
                    : "bg-bg text-text-secondary hover:text-text border border-border"
                }`}
              >
                {style}
              </button>
            ))}
          </div>
        </div>
      )}
    </form>
  );
}
