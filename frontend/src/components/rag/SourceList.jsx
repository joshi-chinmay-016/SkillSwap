import React from "react";
import { FileText, Layers, Bookmark } from "lucide-react";

export default function SourceList({ sources = [] }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="space-y-3 pt-2">
      <div className="flex items-center gap-2 text-xs font-bold text-text-secondary uppercase tracking-wider">
        <Bookmark size={14} className="text-accent" />
        <span>Supporting Knowledge Sources ({sources.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {sources.map((src) => (
          <div
            key={`${src.document_id}-${src.chunk_id}`}
            className="p-3.5 bg-bg border border-border rounded-xl shadow-sm hover:border-accent/40 transition-all flex flex-col justify-between"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <FileText size={15} className="text-accent shrink-0" />
                <span className="text-xs font-semibold text-text truncate" title={src.document_name}>
                  {src.document_name || "Document"}
                </span>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-accent/10 text-accent border border-accent/20 shrink-0">
                Rank #{src.rank}
              </span>
            </div>

            <div className="mt-2.5 pt-2 border-t border-border/50 flex items-center justify-between text-[11px] text-text-secondary font-mono">
              <div className="flex items-center gap-1">
                <Layers size={11} />
                <span>Chunk ID: {src.chunk_id.slice(0, 8)}...</span>
              </div>
              <span>Relevance: {(src.score * 100).toFixed(1)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
