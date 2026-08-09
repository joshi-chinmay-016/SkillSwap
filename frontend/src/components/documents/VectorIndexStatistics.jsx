import React from "react";
import { Database, CheckCircle2, Layers, AlertCircle, HardDrive } from "lucide-react";

/**
 * Renders backend-driven FAISS Vector Store statistics for a document.
 */
export default function VectorIndexStatistics({ vectorStatus }) {
  if (!vectorStatus) return null;

  const {
    total_embeddings = 0,
    indexed = 0,
    failed = 0,
    remaining = 0,
    index_size = 0,
    dimension = 768,
    index_type = "FAISS CPU (IndexIDMap2 + IndexFlatIP)",
  } = vectorStatus;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
        <span className="text-[10px] font-extrabold uppercase text-slate-500 flex items-center gap-1 mb-1">
          <Database size={11} className="text-indigo-500" />
          Indexed Vectors
        </span>
        <div className="text-sm font-black text-slate-900 dark:text-white">
          {indexed.toLocaleString()} / {total_embeddings.toLocaleString()}
        </div>
      </div>

      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
        <span className="text-[10px] font-extrabold uppercase text-slate-500 flex items-center gap-1 mb-1">
          <Layers size={11} className="text-teal-500" />
          Index Dimension
        </span>
        <div className="text-sm font-black text-slate-900 dark:text-white">
          {dimension} <span className="text-[10px] font-semibold text-slate-500">float32</span>
        </div>
      </div>

      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
        <span className="text-[10px] font-extrabold uppercase text-slate-500 flex items-center gap-1 mb-1">
          <HardDrive size={11} className="text-purple-500" />
          Global Store Size
        </span>
        <div className="text-sm font-black text-slate-900 dark:text-white">
          {index_size.toLocaleString()} <span className="text-[10px] font-semibold text-slate-500">vectors</span>
        </div>
      </div>

      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
        <span className="text-[10px] font-extrabold uppercase text-slate-500 flex items-center gap-1 mb-1">
          <AlertCircle size={11} className={failed > 0 ? "text-red-500" : "text-slate-400"} />
          Status Summary
        </span>
        <div className="text-sm font-black text-slate-900 dark:text-white">
          {failed > 0 ? (
            <span className="text-amber-600 dark:text-amber-400">{failed} Failed</span>
          ) : (
            <span className="text-emerald-600 dark:text-emerald-400">All Persisted</span>
          )}
        </div>
      </div>
    </div>
  );
}
