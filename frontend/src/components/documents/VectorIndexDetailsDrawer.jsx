import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, Database, Shield, Layers, HardDrive, Cpu, CheckCircle2, ArrowRight } from "lucide-react";

/**
 * Technical specification drawer for FAISS Vector Storage.
 */
export default function VectorIndexDetailsDrawer({ isOpen, onClose, vectorStatus }) {
  if (!isOpen || !vectorStatus) return null;

  const {
    document_id = "",
    status = "INDEXED",
    total_embeddings = 0,
    indexed = 0,
    failed = 0,
    remaining = 0,
    index_size = 0,
    dimension = 768,
    index_type = "FAISS CPU (IndexIDMap2 + IndexFlatIP)",
    last_indexed_at = null,
  } = vectorStatus;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
        />

        {/* Sliding Panel */}
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 220 }}
          className="relative z-10 w-full max-w-md bg-white dark:bg-slate-900 shadow-2xl border-l border-slate-200 dark:border-slate-800 flex flex-col h-full overflow-hidden"
        >
          {/* Top Header */}
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/90">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 font-black">
                <Database size={18} />
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-white">
                  FAISS Vector Store Specs
                </h3>
                <p className="text-xs text-slate-500 font-semibold">
                  Technical Architecture & Index Metrics
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Drawer Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
            {/* Index Specification Box */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-2.5">
              <h4 className="text-xs font-black uppercase text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5">
                <HardDrive size={13} />
                Index Specification
              </h4>

              <div className="space-y-1.5 font-medium text-slate-700 dark:text-slate-300">
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">Vector Store Engine</span>
                  <span className="font-bold text-slate-900 dark:text-white">FAISS CPU</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">FAISS Index Type</span>
                  <span className="font-bold text-slate-900 dark:text-white">IndexIDMap2(IndexFlatIP)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">Embedding Dimension</span>
                  <span className="font-bold text-slate-900 dark:text-white">{dimension} float32</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">Vector ID Mapping</span>
                  <span className="font-bold text-slate-900 dark:text-white">SHA-256 (63-bit int64)</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Similarity Metric</span>
                  <span className="font-bold text-slate-900 dark:text-white">Cosine / Inner Product</span>
                </div>
              </div>
            </div>

            {/* Document Index Metrics */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-2.5">
              <h4 className="text-xs font-black uppercase text-teal-600 dark:text-teal-400 flex items-center gap-1.5">
                <Layers size={13} />
                Document Index Metrics
              </h4>

              <div className="space-y-1.5 font-medium text-slate-700 dark:text-slate-300">
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">Document Status</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">{status}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">Indexed Vectors</span>
                  <span className="font-bold text-slate-900 dark:text-white">{indexed.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">Total Eligible Embeddings</span>
                  <span className="font-bold text-slate-900 dark:text-white">{total_embeddings.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/60">
                  <span className="text-slate-500">Failed Vectors</span>
                  <span className="font-bold text-red-600 dark:text-red-400">{failed}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Global FAISS Index Size</span>
                  <span className="font-bold text-slate-900 dark:text-white">{index_size.toLocaleString()} vectors</span>
                </div>
              </div>
            </div>

            {/* Architecture Pipeline Flow Explanation */}
            <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/60 space-y-2">
              <h4 className="text-xs font-black text-indigo-700 dark:text-indigo-300 flex items-center gap-1.5">
                <Cpu size={13} />
                Indexing Data Flow
              </h4>

              <div className="flex items-center gap-1.5 text-[11px] font-bold text-indigo-900 dark:text-indigo-200">
                <span>READY Embeddings</span>
                <ArrowRight size={10} />
                <span>Validation</span>
                <ArrowRight size={10} />
                <span>SHA-256 ID</span>
                <ArrowRight size={10} />
                <span>FAISS Index</span>
              </div>

              <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                PostgreSQL remains the source of truth for chunk text, ownership, and metadata. FAISS provides persistent vector indexing optimized for fast similarity search during future retrieval.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
