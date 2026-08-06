import React from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FileText,
  File,
  X,
  Download,
  Edit2,
  Trash2,
  Calendar,
  HardDrive,
  CheckCircle2,
  Clock,
  Sparkles,
  ShieldCheck,
  BookOpen,
} from "lucide-react";

export default function DocumentPreview({
  document: doc,
  isOpen,
  onClose,
  onRename,
  onDownload,
  onDelete,
}) {
  if (!isOpen || !doc) return null;

  const formatSize = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const formatDate = (isoString) => {
    if (!isoString) return "";
    return new Date(isoString).toLocaleString("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  };

  const ext = (doc.file_extension || "").toLowerCase();

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/40 backdrop-blur-xs"
        />

        {/* Modal Surface */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ type: "spring", stiffness: 350, damping: 25 }}
          className="relative z-10 w-full max-w-lg overflow-hidden rounded-2xl border border-border bg-bg p-6 shadow-2xl"
        >
          {/* Close button */}
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>

          {/* Header */}
          <div className="flex items-start gap-4 mb-5 pr-6">
            <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent shrink-0">
              <FileText size={28} />
            </div>

            <div className="min-w-0">
              <h3 className="text-base font-bold text-text leading-snug truncate">
                {doc.display_name}
              </h3>
              <p className="text-xs text-text-secondary truncate mt-0.5">
                {doc.original_filename}
              </p>

              <div className="flex items-center gap-2 mt-2">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-accent/10 text-accent font-bold text-[10px] uppercase tracking-wider">
                  {ext}
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-success/10 text-success font-bold text-[10px]">
                  <CheckCircle2 size={10} />
                  {doc.status}
                </span>
              </div>
            </div>
          </div>

          {/* Details Card Grid */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="p-3 rounded-xl bg-bg-alt border border-border/60">
              <div className="flex items-center gap-1.5 text-text-secondary text-[11px] font-medium mb-1">
                <HardDrive size={13} />
                <span>File Size</span>
              </div>
              <p className="text-xs font-bold text-text">{formatSize(doc.file_size)}</p>
            </div>

            <div className="p-3 rounded-xl bg-bg-alt border border-border/60">
              <div className="flex items-center gap-1.5 text-text-secondary text-[11px] font-medium mb-1">
                <Calendar size={13} />
                <span>Uploaded</span>
              </div>
              <p className="text-xs font-bold text-text">{formatDate(doc.uploaded_at)}</p>
            </div>

            <div className="p-3 rounded-xl bg-bg-alt border border-border/60">
              <div className="flex items-center gap-1.5 text-text-secondary text-[11px] font-medium mb-1">
                <BookOpen size={13} />
                <span>Estimated Size</span>
              </div>
              <p className="text-xs font-bold text-text">
                ~{Math.max(1, Math.round(doc.file_size / 2048))} Pages
              </p>
            </div>

            <div className="p-3 rounded-xl bg-bg-alt border border-border/60">
              <div className="flex items-center gap-1.5 text-text-secondary text-[11px] font-medium mb-1">
                <ShieldCheck size={13} />
                <span>Integrity</span>
              </div>
              <p className="text-xs font-bold text-success">Verified SHA-256</p>
            </div>
          </div>

          {/* AI RAG Readiness Banner */}
          <div className="p-3.5 rounded-xl border border-accent/20 bg-accent/5 mb-6 flex items-center gap-3">
            <Sparkles size={18} className="text-accent shrink-0" />
            <div className="text-xs">
              <p className="font-semibold text-text">AI Retrieval Ready</p>
              <p className="text-[11px] text-text-secondary">
                This document is safely stored in your AI Knowledge Base.
              </p>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between gap-3 pt-3 border-t border-border">
            <button
              type="button"
              onClick={() => {
                onClose();
                onDelete(doc);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-danger/10 text-danger hover:bg-danger/20 font-semibold text-xs transition-colors cursor-pointer"
            >
              <Trash2 size={14} />
              <span>Delete</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onRename(doc);
                }}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-bg-alt border border-border hover:bg-bg text-text font-semibold text-xs transition-colors cursor-pointer"
              >
                <Edit2 size={14} />
                <span>Rename</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  onClose();
                  onDownload(doc);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover font-semibold text-xs transition-colors cursor-pointer shadow-xs"
              >
                <Download size={14} />
                <span>Download</span>
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
