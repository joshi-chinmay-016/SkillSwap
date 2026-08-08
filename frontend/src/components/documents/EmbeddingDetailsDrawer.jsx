import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, Cpu, CheckCircle2, AlertTriangle, Layers, Clock, ShieldCheck, Tag } from "lucide-react";

export default function EmbeddingDetailsDrawer({ chunk, embeddingMeta, onClose }) {
  if (!chunk) return null;

  const status = embeddingMeta?.status || (chunk.status === "READY" ? "READY" : "PENDING");
  const modelName = embeddingMeta?.model_name || embeddingMeta?.model || "text-embedding-004";
  const modelVersion = embeddingMeta?.model_version || "v1";
  const provider = embeddingMeta?.provider || "gemini";
  const dimension = embeddingMeta?.dimension || 768;
  const embeddingVersion = embeddingMeta?.embedding_version || 1;

  let statusBadge = (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-black bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
      <CheckCircle2 size={13} />
      Ready
    </span>
  );

  if (status === "PROCESSING" || status === "PENDING") {
    statusBadge = (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-black bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border border-purple-500/20 animate-pulse">
        <Clock size={13} />
        {status}
      </span>
    );
  } else if (status === "FAILED") {
    statusBadge = (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-black bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300 border border-red-500/20">
        <AlertTriangle size={13} />
        Failed
      </span>
    );
  }

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

        {/* Drawer Container */}
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className="relative z-10 w-full max-w-md bg-white dark:bg-slate-900 h-full shadow-2xl border-l border-slate-200 dark:border-slate-800 flex flex-col"
        >
          {/* Header */}
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/90">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-600/10 dark:bg-indigo-400/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-black text-sm">
                <Cpu size={18} />
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-white">
                  Embedding Metadata
                </h3>
                <p className="text-[11px] text-slate-500 font-semibold">
                  Chunk #{chunk.chunk_index} Vector Details
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
            {/* Status and Provider Header Card */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                  Lifecycle Status
                </span>
                {statusBadge}
              </div>
              <div className="text-right">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                  Provider
                </span>
                <span className="text-sm font-extrabold text-slate-800 dark:text-slate-200 capitalize">
                  {provider}
                </span>
              </div>
            </div>

            {/* Properties Table */}
            <div className="space-y-2 rounded-xl border border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900 text-xs">
              <h4 className="font-extrabold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[11px] mb-3 flex items-center gap-1.5">
                <Tag size={13} className="text-indigo-500" />
                Technical Identity
              </h4>

              <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500 font-semibold">Chunk Index</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  #{chunk.chunk_index}
                </span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500 font-semibold">Model Name</span>
                <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                  {modelName}
                </span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500 font-semibold">Model Version</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {modelVersion}
                </span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500 font-semibold">Embedding Version</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  v{embeddingVersion}
                </span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500 font-semibold">Dimensions</span>
                <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                  {dimension} values
                </span>
              </div>

              <div className="flex justify-between py-2">
                <span className="text-slate-500 font-semibold">Estimated Tokens</span>
                <span className="font-mono font-bold text-purple-600 dark:text-purple-400">
                  ~{chunk.estimated_tokens || 0} tokens
                </span>
              </div>
            </div>

            {/* Privacy & Educational Note */}
            <div className="p-4 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/60 text-xs text-indigo-900 dark:text-indigo-200 space-y-2">
              <div className="flex items-center gap-1.5 font-bold text-indigo-700 dark:text-indigo-300">
                <ShieldCheck size={16} />
                Vector Representation Privacy
              </div>
              <p className="leading-relaxed text-[11px]">
                Embeddings transform knowledge chunks into mathematical vectors for downstream retrieval.
                Raw vector data is stored securely in the database and is excluded from user-facing APIs for privacy and efficiency.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
