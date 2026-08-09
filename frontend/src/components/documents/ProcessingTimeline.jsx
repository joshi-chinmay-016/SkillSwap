import React from "react";
import { motion } from "motion/react";
import { Check, Upload, FileText, Scissors, Cpu, Database, Sparkles, AlertTriangle } from "lucide-react";

/**
 * 6-stage AI Knowledge Pipeline stages:
 * 1. Upload
 * 2. Parsing
 * 3. Chunking
 * 4. Embeddings
 * 5. Vector Index
 * 6. Ready for AI
 */
const PIPELINE_STAGES = [
  { id: "upload", label: "Upload", icon: Upload },
  { id: "parsing", label: "Parsing", icon: FileText },
  { id: "chunking", label: "Chunking", icon: Scissors },
  { id: "embeddings", label: "Embeddings", icon: Cpu },
  { id: "vector", label: "Vector Index", icon: Database },
  { id: "ready", label: "Ready for AI", icon: Sparkles },
];

export default function ProcessingTimeline({
  documentStatus = "UPLOADED",
  embeddingStatus = null,
  vectorStatus = null,
  compact = false,
}) {
  // Determine current active step index based on backend Document.status, embeddingStatus & vectorStatus
  let activeIndex = 0;
  let isFailed = false;

  if (documentStatus === "FAILED") {
    isFailed = true;
    activeIndex = 2; // Failed during chunking/parsing
  } else if (documentStatus === "READY") {
    const embeddingsDone =
      embeddingStatus &&
      embeddingStatus.ready > 0 &&
      embeddingStatus.ready === embeddingStatus.total_active;

    const vectorIndexed =
      vectorStatus &&
      (vectorStatus.status === "INDEXED" ||
        (vectorStatus.total_embeddings > 0 && vectorStatus.indexed === vectorStatus.total_embeddings));

    const vectorFailed = vectorStatus && vectorStatus.status === "INDEX_FAILED";

    if (vectorIndexed) {
      activeIndex = 5; // Ready for AI (stage index 5)
    } else if (vectorFailed) {
      isFailed = true;
      activeIndex = 4; // Vector Index failed (stage index 4)
    } else if (vectorStatus && (vectorStatus.status === "INDEXING" || vectorStatus.indexed > 0)) {
      activeIndex = 4; // Vector Index in progress/partial (stage index 4)
    } else if (embeddingsDone) {
      activeIndex = 4; // Embeddings completed -> Vector Index stage pending/active (stage index 4)
    } else if (embeddingStatus && embeddingStatus.ready > 0) {
      activeIndex = 3; // Embeddings stage active
    } else if (embeddingStatus && embeddingStatus.failed > 0 && embeddingStatus.ready === 0) {
      isFailed = true;
      activeIndex = 3; // Embeddings stage failed
    } else if (embeddingStatus && (embeddingStatus.processing > 0 || embeddingStatus.pending > 0)) {
      activeIndex = 3; // Embeddings processing
    } else {
      activeIndex = 2; // Chunking ready, Embeddings pending
    }
  } else if (documentStatus === "PROCESSING") {
    activeIndex = 1; // In parsing phase
  } else {
    activeIndex = 0; // Uploaded
  }

  return (
    <div className={`w-full ${compact ? "py-2" : "py-3 px-1"}`}>
      <div className="flex items-center justify-between relative">
        {/* Background Connecting Line */}
        <div className="absolute top-3.5 left-4 right-4 h-0.5 bg-slate-200 dark:bg-slate-700 -translate-y-1/2 z-0" />

        {/* Animated Progress Connecting Line */}
        <motion.div
          className={`absolute top-3.5 left-4 h-0.5 -translate-y-1/2 z-0 ${
            isFailed ? "bg-red-500" : "bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500"
          }`}
          initial={{ width: "0%" }}
          animate={{
            width: `${(activeIndex / (PIPELINE_STAGES.length - 1)) * 100}%`,
          }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />

        {/* Stage Nodes */}
        {PIPELINE_STAGES.map((stage, idx) => {
          const isCompleted = idx < activeIndex || (idx === activeIndex && activeIndex === 3 && embeddingStatus && embeddingStatus.ready > 0 && embeddingStatus.ready === embeddingStatus.total_active);
          const isCurrent = idx === activeIndex && !isCompleted && !isFailed;
          const isFailedStep = isFailed && idx === activeIndex;

          const IconComponent = stage.icon;

          return (
            <div key={stage.id} className="relative z-10 flex flex-col items-center">
              {/* Node Circle */}
              <motion.div
                initial={false}
                animate={{
                  scale: isCurrent ? 1.15 : 1,
                }}
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors shadow-sm ${
                  isFailedStep
                    ? "bg-red-500 text-white border-2 border-red-600"
                    : isCompleted
                    ? "bg-emerald-500 text-white border-2 border-emerald-600"
                    : isCurrent
                    ? "bg-indigo-600 text-white border-2 border-indigo-400 animate-pulse"
                    : "bg-white dark:bg-slate-800 border-2 border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-400"
                }`}
              >
                {isFailedStep ? (
                  <AlertTriangle size={12} />
                ) : isCompleted ? (
                  <Check size={13} strokeWidth={3} />
                ) : (
                  <IconComponent size={12} />
                )}
              </motion.div>

              {/* Stage Label (Day numbers removed as requested) */}
              {!compact && (
                <div className="mt-2 text-center">
                  <span
                    className={`block text-[11px] font-bold tracking-tight whitespace-nowrap ${
                      isFailedStep
                        ? "text-red-600 dark:text-red-400"
                        : isCompleted
                        ? "text-emerald-700 dark:text-emerald-400 font-extrabold"
                        : isCurrent
                        ? "text-indigo-600 dark:text-indigo-400 font-black"
                        : "text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
