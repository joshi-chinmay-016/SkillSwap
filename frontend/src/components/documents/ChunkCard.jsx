import React from "react";
import { motion } from "motion/react";
import { Layers, FileText, Hash, CheckCircle2, ChevronRight } from "lucide-react";

export default function ChunkCard({ chunk, onClick, isSelected = false }) {
  const previewText = chunk.chunk_text
    ? chunk.chunk_text.slice(0, 140) + (chunk.chunk_text.length > 140 ? "..." : "")
    : "No text preview available.";

  return (
    <motion.div
      whileHover={{ scale: 1.015, y: -2 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className={`p-4 rounded-xl border transition-all duration-150 cursor-pointer ${
        isSelected
          ? "bg-indigo-50/90 dark:bg-indigo-950/70 border-indigo-500 shadow-md ring-2 ring-indigo-500/20"
          : "bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 hover:border-indigo-300 dark:hover:border-indigo-700 shadow-xs hover:shadow-md"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 text-xs font-black">
            <Hash size={11} />
            Chunk #{chunk.chunk_index}
          </span>

          {chunk.section && (
            <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 truncate max-w-[160px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">
              {chunk.section}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 text-[10px] font-black text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/80 px-2 py-0.5 rounded-full border border-emerald-500/20">
            <CheckCircle2 size={10} />
            Embedded
          </span>
          <span className="text-[11px] font-extrabold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/50 px-2 py-0.5 rounded-md">
            ~{chunk.estimated_tokens} tokens
          </span>
          <ChevronRight size={14} className="text-slate-400" />
        </div>
      </div>

      {/* Text Preview */}
      <p className="text-xs text-slate-600 dark:text-slate-300 font-mono leading-relaxed line-clamp-2 bg-slate-50 dark:bg-slate-950/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800/80">
        "{previewText}"
      </p>

      {/* Footer Info */}
      <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-400 font-semibold">
        <span>
          Offsets: {chunk.start_offset} – {chunk.end_offset}
        </span>
        <span className="capitalize">{chunk.strategy || "recursive"}</span>
      </div>
    </motion.div>
  );
}
