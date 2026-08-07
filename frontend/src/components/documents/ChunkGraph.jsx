import React from "react";
import { motion } from "motion/react";
import { FileText, Layers, Cpu, CheckCircle2, ArrowRight } from "lucide-react";

export default function ChunkGraph({ totalChunks = 4, isProcessing = false, documentName = "Parsed Document" }) {
  // Show 4 representative chunk nodes
  const visibleNodes = [1, 2, 3, 4];

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-900 text-white p-5 my-4 shadow-lg">
      {/* Background Glow */}
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-emerald-500/10 pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-indigo-400" />
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-300">
              AI Knowledge Flow Graph
            </h4>
          </div>
          <span className="text-[11px] font-bold text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700">
            {totalChunks} Chunks Generated
          </span>
        </div>

        {/* Node Flow Diagram */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-2">
          {/* Node 1: Parsed Document */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex flex-col items-center p-3 rounded-xl bg-slate-800/90 border border-indigo-500/40 text-center min-w-[120px] shadow-md"
          >
            <div className="w-10 h-10 rounded-full bg-indigo-600/30 border border-indigo-400 flex items-center justify-center mb-1 text-indigo-300">
              <FileText size={18} />
            </div>
            <span className="text-[11px] font-extrabold truncate max-w-[110px] text-slate-200">
              {documentName}
            </span>
            <span className="text-[9px] font-bold text-emerald-400">Parsed Text</span>
          </motion.div>

          <ArrowRight className="text-slate-600 hidden sm:block shrink-0" size={16} />

          {/* Node 2 Group: Chunks */}
          <div className="flex flex-wrap items-center justify-center gap-2 max-w-xs">
            {visibleNodes.map((n, idx) => (
              <motion.div
                key={n}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{
                  opacity: 1,
                  scale: isProcessing ? [1, 1.08, 1] : 1,
                }}
                transition={{
                  duration: 2,
                  repeat: isProcessing ? Infinity : 0,
                  delay: idx * 0.2,
                }}
                whileHover={{ scale: 1.1 }}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-950/80 border border-indigo-500/50 text-indigo-200 text-xs font-bold shadow-sm"
              >
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Chunk #{n}</span>
              </motion.div>
            ))}
          </div>

          <ArrowRight className="text-slate-600 hidden sm:block shrink-0" size={16} />

          {/* Node 3: Embeddings (Future readiness indicator) */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex flex-col items-center p-3 rounded-xl bg-slate-800/60 border border-purple-500/30 text-center min-w-[120px] opacity-75"
          >
            <div className="w-10 h-10 rounded-full bg-purple-900/40 border border-purple-500/40 flex items-center justify-center mb-1 text-purple-300">
              <Cpu size={18} />
            </div>
            <span className="text-[11px] font-extrabold text-slate-300">Embeddings</span>
            <span className="text-[9px] font-bold text-purple-400">Next Stage</span>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
