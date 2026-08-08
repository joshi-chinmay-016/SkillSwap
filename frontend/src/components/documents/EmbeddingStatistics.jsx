import React from "react";
import { Cpu, Layers, CheckCircle2, Clock, AlertTriangle, Hash } from "lucide-react";

export default function EmbeddingStatistics({ embeddingStatus }) {
  if (!embeddingStatus) {
    return (
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-500">
        Embedding statistics unavailable.
      </div>
    );
  }

  const {
    model = "text-embedding-004",
    dimension = 768,
    ready = 0,
    pending = 0,
    processing = 0,
    failed = 0,
    archived = 0,
    total_active = 0,
  } = embeddingStatus;

  const remaining = pending + processing;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {/* Total Active Chunks */}
      <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
        <div className="flex items-center gap-2 text-slate-500 mb-1">
          <Layers size={14} className="text-indigo-500" />
          <span className="text-[11px] font-bold uppercase tracking-wider">Total Chunks</span>
        </div>
        <span className="text-xl font-black text-slate-900 dark:text-white">
          {total_active}
        </span>
      </div>

      {/* Ready / Embedded */}
      <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
        <div className="flex items-center gap-2 text-slate-500 mb-1">
          <CheckCircle2 size={14} className="text-emerald-500" />
          <span className="text-[11px] font-bold uppercase tracking-wider">Embedded</span>
        </div>
        <span className="text-xl font-black text-emerald-600 dark:text-emerald-400">
          {ready}
        </span>
      </div>

      {/* Remaining Chunks */}
      <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
        <div className="flex items-center gap-2 text-slate-500 mb-1">
          <Clock size={14} className="text-purple-500" />
          <span className="text-[11px] font-bold uppercase tracking-wider">Remaining</span>
        </div>
        <span className="text-xl font-black text-purple-600 dark:text-purple-400">
          {remaining}
        </span>
      </div>

      {/* Dimension & Model */}
      <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
        <div className="flex items-center gap-2 text-slate-500 mb-1">
          <Cpu size={14} className="text-blue-500" />
          <span className="text-[11px] font-bold uppercase tracking-wider">Dimension</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-xl font-black text-blue-600 dark:text-blue-400">
            {dimension}
          </span>
          <span className="text-[10px] font-bold text-slate-400 truncate max-w-[90px]">
            {model}
          </span>
        </div>
      </div>
    </div>
  );
}
