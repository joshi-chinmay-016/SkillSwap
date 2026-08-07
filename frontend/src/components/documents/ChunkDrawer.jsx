import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, Hash, Layers, Cpu, AlignLeft, CheckCircle2, Bookmark } from "lucide-react";

export default function ChunkDrawer({ chunk, onClose }) {
  if (!chunk) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs"
        />

        {/* Drawer Content */}
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className="relative z-10 w-full max-w-lg bg-white dark:bg-slate-900 h-full shadow-2xl border-l border-slate-200 dark:border-slate-800 flex flex-col"
        >
          {/* Header */}
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/90">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/10 dark:bg-indigo-400/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-black text-sm">
                #{chunk.chunk_index}
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-white">
                  Chunk #{chunk.chunk_index} Details
                </h3>
                <p className="text-[11px] text-slate-500 font-semibold">
                  Intelligent Knowledge Segment
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            {/* Quick Metadata Badges */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Estimated Tokens
                </span>
                <span className="text-base font-extrabold text-purple-600 dark:text-purple-400">
                  ~{chunk.estimated_tokens} tokens
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Character Length
                </span>
                <span className="text-base font-extrabold text-indigo-600 dark:text-indigo-400">
                  {chunk.chunk_text ? chunk.chunk_text.length : 0} chars
                </span>
              </div>
            </div>

            {/* Detailed Properties Table */}
            <div className="space-y-2 rounded-xl border border-slate-200 dark:border-slate-800 p-4 bg-slate-50/50 dark:bg-slate-950/40 text-xs">
              <h4 className="font-extrabold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[11px] mb-3">
                Chunk Properties
              </h4>

              <div className="flex justify-between py-1.5 border-b border-slate-200/60 dark:border-slate-800/60">
                <span className="text-slate-500 font-semibold">Chunk Index:</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {chunk.chunk_index}
                </span>
              </div>

              <div className="flex justify-between py-1.5 border-b border-slate-200/60 dark:border-slate-800/60">
                <span className="text-slate-500 font-semibold">Section / Heading:</span>
                <span className="font-bold text-indigo-600 dark:text-indigo-400">
                  {chunk.section || "General"}
                </span>
              </div>

              <div className="flex justify-between py-1.5 border-b border-slate-200/60 dark:border-slate-800/60">
                <span className="text-slate-500 font-semibold">Start / End Offsets:</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {chunk.start_offset} – {chunk.end_offset}
                </span>
              </div>

              <div className="flex justify-between py-1.5 border-b border-slate-200/60 dark:border-slate-800/60">
                <span className="text-slate-500 font-semibold">Chunk Size Limit:</span>
                <span className="font-bold text-slate-900 dark:text-white">
                  {chunk.chunk_size || 800} chars
                </span>
              </div>

              <div className="flex justify-between py-1.5 border-b border-slate-200/60 dark:border-slate-800/60">
                <span className="text-slate-500 font-semibold">Overlap Halo:</span>
                <span className="font-bold text-slate-900 dark:text-white">
                  {chunk.overlap_size || 150} chars
                </span>
              </div>

              <div className="flex justify-between py-1.5 border-b border-slate-200/60 dark:border-slate-800/60">
                <span className="text-slate-500 font-semibold">Chunk Strategy:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400 capitalize">
                  {chunk.strategy || "recursive"}
                </span>
              </div>

              <div className="flex justify-between py-1.5">
                <span className="text-slate-500 font-semibold">Strategy Version:</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  v{chunk.strategy_version || "1.0.0"}
                </span>
              </div>
            </div>

            {/* Chunk Text Preview Box */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-extrabold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[11px]">
                  Chunk Text Preview
                </h4>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                  <CheckCircle2 size={12} /> Normalized Text
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 text-slate-200 font-mono text-xs leading-relaxed border border-slate-800 overflow-x-auto max-h-64 whitespace-pre-wrap select-all">
                {chunk.chunk_text || "No text available."}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
