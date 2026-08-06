import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, FileText, Hash, Clock, HardDrive, Calendar, ShieldCheck, Sparkles, AlertCircle } from "lucide-react";
import { useParsingStatus } from "../../hooks/useDocuments";
import ProcessingTimeline from "./ProcessingTimeline";

export default function MetadataDrawer({ document, isOpen, onClose }) {
  const { data: parsedData, isLoading: isParsingLoading } = useParsingStatus(
    document?.id,
    isOpen
  );

  if (!document || !isOpen) return null;

  const charCount = parsedData?.text_content ? parsedData.text_content.length : 0;
  const wordCount = charCount ? Math.round(charCount / 5) : 0;
  const readingTimeMinutes = wordCount ? Math.max(1, Math.round(wordCount / 200)) : 0;

  const formatBytes = (bytes) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Drawer Panel */}
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 220 }}
          className="relative w-full max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 p-6 shadow-2xl flex flex-col justify-between overflow-y-auto z-50 text-slate-900 dark:text-slate-100"
        >
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400">
                  <FileText size={22} />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900 dark:text-white truncate max-w-[240px]">
                    {document.display_name}
                  </h3>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase tracking-wider font-bold">
                    .{document.file_extension} document
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X size={20} />
              </button>
            </div>

            {/* AI Processing Timeline */}
            <div className="bg-slate-50 dark:bg-slate-850 p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800">
              <h4 className="text-xs font-black text-slate-900 dark:text-white uppercase tracking-wider mb-2">
                AI Knowledge Pipeline
              </h4>
              <ProcessingTimeline documentStatus={document.status} compact={false} />
            </div>

            {/* Document Statistics Grid */}
            <div className="space-y-3">
              <h4 className="text-xs font-black text-slate-900 dark:text-white uppercase tracking-wider">
                Document Metadata & Metrics
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-[11px] font-bold">
                    <Hash size={14} className="text-indigo-500" />
                    <span>Character Count</span>
                  </div>
                  <p className="text-base font-extrabold text-slate-900 dark:text-white">
                    {charCount > 0 ? charCount.toLocaleString() : isParsingLoading ? "Loading..." : "N/A"}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-[11px] font-bold">
                    <FileText size={14} className="text-emerald-500" />
                    <span>Estimated Words</span>
                  </div>
                  <p className="text-base font-extrabold text-slate-900 dark:text-white">
                    {wordCount > 0 ? wordCount.toLocaleString() : isParsingLoading ? "Loading..." : "N/A"}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-[11px] font-bold">
                    <Clock size={14} className="text-amber-500" />
                    <span>Est. Reading Time</span>
                  </div>
                  <p className="text-base font-extrabold text-slate-900 dark:text-white">
                    {readingTimeMinutes > 0 ? `${readingTimeMinutes} min` : "N/A"}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-[11px] font-bold">
                    <HardDrive size={14} className="text-purple-500" />
                    <span>File Size</span>
                  </div>
                  <p className="text-base font-extrabold text-slate-900 dark:text-white">
                    {formatBytes(document.file_size)}
                  </p>
                </div>
              </div>
            </div>

            {/* Technical Information */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-bold">Parser Version</span>
                <span className="font-extrabold text-slate-900 dark:text-white font-mono">v1.0 Engine</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-bold">MIME Type</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{document.mime_type}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-bold">Uploaded On</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {new Date(document.uploaded_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-bold">Status</span>
                <span
                  className={`font-black ${
                    document.status === "READY"
                      ? "text-emerald-600 dark:text-emerald-400"
                      : document.status === "FAILED"
                      ? "text-red-600 dark:text-red-400"
                      : "text-indigo-600 dark:text-indigo-400"
                  }`}
                >
                  {document.status}
                </span>
              </div>
            </div>
          </div>

          {/* Drawer Footer */}
          <div className="pt-4 mt-6 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="w-full py-3 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-bold text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer shadow-xs"
            >
              Close Drawer
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
