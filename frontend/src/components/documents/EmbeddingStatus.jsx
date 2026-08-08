import React from "react";
import { motion } from "motion/react";
import { Cpu, CheckCircle2, AlertTriangle, RefreshCw, Layers, Sparkles, ArrowRight } from "lucide-react";

import EmbeddingProgressRing from "./EmbeddingProgressRing";
import EmbeddingStatistics from "./EmbeddingStatistics";
import { useEmbeddingStatus, useReembedDocument, useRetryEmbeddings } from "../../hooks/useDocuments";

export default function EmbeddingStatus({ documentId, documentStatus = "READY" }) {
  const { data: embeddingStatus, isLoading, isError } = useEmbeddingStatus(documentId);
  const reembedMutation = useReembedDocument();
  const retryMutation = useRetryEmbeddings();

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

  if (isError || !embeddingStatus) {
    return null;
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

  const isCompleted = total_active > 0 && ready === total_active;
  const isProcessing = processing > 0 || pending > 0;
  const isFailed = failed > 0 && ready === 0;
  const isPartial = failed > 0 && ready > 0;

  const progressPercent = total_active > 0 ? (ready / total_active) * 100 : 0;

  const handleReembed = () => {
    reembedMutation.mutate(documentId);
  };

  const handleRetry = () => {
    retryMutation.mutate(documentId);
  };

  return (
    <div className="space-y-4">
      {/* Main Embedding Status Card */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Left info & progress */}
          <div className="flex items-center gap-4">
            <EmbeddingProgressRing
              progress={progressPercent}
              status={isFailed ? "FAILED" : isCompleted ? "READY" : "PROCESSING"}
              size={68}
            />

            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-black uppercase tracking-wider text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                  <Cpu size={14} />
                  AI Embeddings Engine
                </span>

                {isCompleted && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                    Ready for Indexing
                  </span>
                )}
                {isProcessing && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 animate-pulse">
                    Processing
                  </span>
                )}
                {isFailed && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300">
                    Failed
                  </span>
                )}
              </div>

              <h4 className="text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
                {isCompleted
                  ? "✓ Embeddings Generated"
                  : isProcessing
                  ? "Generating AI Embeddings..."
                  : isFailed
                  ? "Embedding Generation Failed"
                  : "AI Embeddings"}
              </h4>

              <p className="text-xs text-slate-500 font-semibold mt-0.5">
                {ready} / {total_active} chunks processed ({Math.round(progressPercent)}%)
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
                {retryMutation.isPending ? "Retrying..." : "Retry Failed"}
              </button>
            )}

            <button
              onClick={handleReembed}
              disabled={reembedMutation.isPending}
              className="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-indigo-600 hover:text-white dark:hover:bg-indigo-600 text-slate-700 dark:text-slate-200 text-xs font-extrabold flex items-center gap-1.5 transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw size={13} className={reembedMutation.isPending ? "animate-spin" : ""} />
              {reembedMutation.isPending ? "Re-embedding..." : "Re-embed All"}
            </button>
          </div>
        </div>

        {/* Visual Progress Bar */}
        <div className="mt-4 w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
          <motion.div
            className={`h-full ${
              isFailed
                ? "bg-red-500"
                : isCompleted
                ? "bg-emerald-500"
                : "bg-gradient-to-r from-indigo-500 to-purple-500"
            }`}
            initial={{ width: "0%" }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Embedding Statistics Grid */}
      <EmbeddingStatistics embeddingStatus={embeddingStatus} />
    </div>
  );
}
