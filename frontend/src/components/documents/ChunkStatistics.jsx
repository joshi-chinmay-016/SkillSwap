import React from "react";
import { motion } from "motion/react";
import { Cpu, Layers, Repeat, Clock, CpuIcon, CheckCircle2 } from "lucide-react";

export default function ChunkStatistics({ metadata, isLoading = false }) {
  if (isLoading || !metadata) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-20 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse border border-slate-200 dark:border-slate-700"
          />
        ))}
      </div>
    );
  }

  // Calculate estimated reading time (approx 200 wpm / 250 tokens per min)
  const totalTokens = metadata.total_estimated_tokens || 0;
  const minutes = Math.max(1, Math.round(totalTokens / 250));
  const readingTime = minutes >= 60 ? `${(minutes / 60).toFixed(1)}h` : `${minutes}m`;

  const stats = [
    {
      label: "Total Chunks",
      value: metadata.total_chunks || 0,
      icon: Layers,
      color: "text-indigo-600 dark:text-indigo-400",
      bg: "bg-indigo-50 dark:bg-indigo-950/60 border-indigo-200 dark:border-indigo-800",
    },
    {
      label: "Avg Size",
      value: `${Math.round(metadata.average_chunk_tokens || 0)} Tokens`,
      icon: Cpu,
      color: "text-purple-600 dark:text-purple-400",
      bg: "bg-purple-50 dark:bg-purple-950/60 border-purple-200 dark:border-purple-800",
    },
    {
      label: "Overlap",
      value: `${metadata.overlap_size || 150} Chars`,
      icon: Repeat,
      color: "text-blue-600 dark:text-blue-400",
      bg: "bg-blue-50 dark:bg-blue-950/60 border-blue-200 dark:border-blue-800",
    },
    {
      label: "Reading Time",
      value: readingTime,
      icon: Clock,
      color: "text-emerald-600 dark:text-emerald-400",
      bg: "bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-800",
    },
  ];

  return (
    <div className="space-y-3 my-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: idx * 0.05 }}
              className={`p-3.5 rounded-xl border ${stat.bg} shadow-xs flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {stat.label}
                </span>
                <Icon size={16} className={stat.color} />
              </div>
              <div className="mt-2 text-lg font-black text-slate-900 dark:text-white tracking-tight">
                {stat.value}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Strategy Badge */}
      <div className="flex items-center justify-between text-xs px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
          <span>
            Strategy: <strong className="text-slate-900 dark:text-white capitalize">{metadata.strategy || "Recursive"}</strong> (v{metadata.strategy_version || "1.0.0"})
          </span>
        </div>
        <span>
          Target Size: <strong className="text-slate-900 dark:text-white">{metadata.chunk_size || 800} chars</strong>
        </span>
      </div>
    </div>
  );
}
