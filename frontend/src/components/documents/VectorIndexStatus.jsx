import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Database, CheckCircle2, AlertTriangle, RefreshCw, Info, ChevronDown, ChevronUp, Layers } from "lucide-react";
import VectorIndexProgressRing from "./VectorIndexProgressRing";
import VectorIndexStatistics from "./VectorIndexStatistics";
import VectorIndexDetailsDrawer from "./VectorIndexDetailsDrawer";
import { useVectorIndexStatus, useIndexVectors, useRetryVectorIndexing } from "../../hooks/useDocuments";

/**
 * Premium card component for displaying FAISS Vector Store status, progress, and operations.
 */
export default function VectorIndexStatus({ documentId }) {
  const { data: vectorStatus, isLoading, isError } = useVectorIndexStatus(documentId);
  const indexMutation = useIndexVectors();
  const retryMutation = useRetryVectorIndexing();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 animate-pulse flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-200 dark:bg-slate-800" />
          <div className="space-y-2">
            <div className="h-4 w-36 bg-slate-200 dark:bg-slate-800 rounded" />
            <div className="h-3 w-24 bg-slate-200 dark:bg-slate-800 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !vectorStatus) {
    return null;
  }

  const {
    status = "PENDING",
    total_embeddings = 0,
    indexed = 0,
    failed = 0,
    remaining = 0,
    index_size = 0,
    dimension = 768,
    index_type = "FAISS CPU (IndexIDMap2 + IndexFlatIP)",
  } = vectorStatus;

  const isCompleted = status === "INDEXED" || (total_embeddings > 0 && indexed === total_embeddings);
  const isIndexing = status === "INDEXING" || remaining > 0;
  const isFailed = status === "INDEX_FAILED";
  const isPartial = status === "PARTIAL";
  const isNoEmbeddings = status === "NO_EMBEDDINGS";

  const progressPercent = total_embeddings > 0 ? (indexed / total_embeddings) * 100 : 0;

  const handleIndex = () => {
    indexMutation.mutate(documentId);
  };

  const handleRetry = () => {
    retryMutation.mutate(documentId);
  };

  return (
    <div className="space-y-4">
      {/* Main Status Card */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Left info & progress ring */}
          <div className="flex items-center gap-4">
            <VectorIndexProgressRing
              progress={progressPercent}
              status={status}
              size={68}
            />

            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-black uppercase tracking-wider text-teal-600 dark:text-teal-400 flex items-center gap-1">
                  <Database size={14} />
                  FAISS Vector Storage
                </span>

                {isCompleted && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                    Vector Index Ready
                  </span>
                )}
                {isIndexing && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 animate-pulse">
                    Indexing...
                  </span>
                )}
                {isPartial && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                    Partial Index
                  </span>
                )}
                {isFailed && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300">
                    Index Failed
                  </span>
                )}
              </div>

              <h4 className="text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
                {isCompleted
                  ? "✓ Vectors Indexed in FAISS"
                  : isIndexing
                  ? "Indexing Vectors into FAISS..."
                  : isPartial
                  ? "Partial Vector Indexing"
                  : isFailed
                  ? "Vector Indexing Failed"
                  : "FAISS Vector Store"}
              </h4>

              <p className="text-xs text-slate-500 font-semibold mt-0.5">
                {indexed.toLocaleString()} / {total_embeddings.toLocaleString()} vectors indexed ({Math.round(progressPercent)}%)
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 self-start md:self-auto">
            {(isFailed || isPartial) && (
              <button
                onClick={handleRetry}
                disabled={retryMutation.isPending}
                className="px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-extrabold flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw size={13} className={retryMutation.isPending ? "animate-spin" : ""} />
                {retryMutation.isPending ? "Retrying..." : "Retry Indexing"}
              </button>
            )}

            {!isCompleted && !isIndexing && !isNoEmbeddings && (
              <button
                onClick={handleIndex}
                disabled={indexMutation.isPending}
                className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-extrabold flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50 cursor-pointer"
              >
                <Database size={13} className={indexMutation.isPending ? "animate-pulse" : ""} />
                {indexMutation.isPending ? "Indexing..." : "Index Vectors"}
              </button>
            )}

            <button
              onClick={() => setIsDrawerOpen(true)}
              className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer"
              title="Vector Store Specs"
            >
              <Info size={16} />
            </button>
          </div>
        </div>

        {/* Visual Progress Bar */}
        <div className="mt-4 w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
          <motion.div
            className={`h-full ${
              isFailed
                ? "bg-red-500"
                : isPartial
                ? "bg-amber-500"
                : isCompleted
                ? "bg-emerald-500"
                : "bg-gradient-to-r from-teal-500 to-indigo-500"
            }`}
            initial={{ width: "0%" }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>

        {/* Partial Success Warning Banner */}
        {isPartial && (
          <div className="mt-3 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-300 font-medium">
            <span className="font-bold">Partial Success:</span> {indexed} vectors successfully indexed. {failed} failed vectors remain available for retry.
          </div>
        )}
      </div>

      {/* Backend Statistics Summary */}
      <VectorIndexStatistics vectorStatus={vectorStatus} />

      {/* Vector Index Technical Specifications Drawer */}
      <VectorIndexDetailsDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        vectorStatus={vectorStatus}
      />
    </div>
  );
}
