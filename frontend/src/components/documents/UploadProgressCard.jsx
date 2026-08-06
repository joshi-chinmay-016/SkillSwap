import React from "react";
import { motion } from "motion/react";
import { FileText, CheckCircle2, AlertTriangle, Loader2, X, RefreshCw } from "lucide-react";

export default function UploadProgressCard({ item, onCancel, onRetry }) {
  const { id, filename, progress, status, error } = item;

  const isSuccess = status === "success";
  const isError = status === "error";
  const isUploading = status === "uploading";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.25 }}
      className={`
        relative overflow-hidden rounded-xl border p-4 shadow-sm transition-all duration-200 bg-bg
        ${isSuccess ? "border-success/40 bg-success/5" : ""}
        ${isError ? "border-danger/40 bg-danger/5" : ""}
        ${isUploading ? "border-accent/40 bg-accent/5" : ""}
      `}
    >
      <div className="flex items-center gap-3">
        {/* Status Icon */}
        <div className="shrink-0">
          {isSuccess && (
            <motion.div
              initial={{ scale: 0.5, rotate: -45 }}
              animate={{ scale: 1, rotate: 0 }}
              className="w-9 h-9 rounded-lg bg-success/15 text-success flex items-center justify-center font-bold"
            >
              <CheckCircle2 size={20} />
            </motion.div>
          )}

          {isError && (
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: [1, 1.1, 1] }}
              className="w-9 h-9 rounded-lg bg-danger/15 text-danger flex items-center justify-center font-bold"
            >
              <AlertTriangle size={20} />
            </motion.div>
          )}

          {isUploading && (
            <div className="w-9 h-9 rounded-lg bg-accent/15 text-accent flex items-center justify-center font-bold">
              <Loader2 size={20} className="animate-spin" />
            </div>
          )}
        </div>

        {/* Info & Progress */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <p className="text-xs font-semibold text-text truncate max-w-[240px] sm:max-w-md">
              {filename}
            </p>
            <span className="text-[11px] font-bold text-text-secondary shrink-0">
              {isSuccess && "Complete!"}
              {isError && "Failed"}
              {isUploading && `${progress}%`}
            </span>
          </div>

          {/* Animated Progress Bar */}
          {isUploading && (
            <div className="h-2 w-full bg-border/60 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="h-full bg-gradient-to-r from-accent to-purple-500 rounded-full"
              />
            </div>
          )}

          {isError && (
            <p className="text-[11px] text-danger mt-0.5 truncate">
              {error || "Upload failed. Please try again."}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="shrink-0 flex items-center gap-1">
          {isError && onRetry && (
            <button
              type="button"
              onClick={() => onRetry(id)}
              className="p-1.5 rounded-lg hover:bg-danger/10 text-danger transition-colors cursor-pointer"
              title="Retry upload"
            >
              <RefreshCw size={15} />
            </button>
          )}

          <button
            type="button"
            onClick={() => onCancel(id)}
            className="p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text transition-colors cursor-pointer"
            title="Dismiss"
          >
            <X size={15} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
