import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { AlertCircle, RefreshCw, X, FileText } from "lucide-react";

export default function RetryDialog({ document, isOpen, onClose, onConfirm }) {
  if (!document || !isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Dialog Content */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-sm bg-surface border border-danger/30 p-6 rounded-2xl shadow-2xl backdrop-blur-xl space-y-4 z-10"
        >
          <div className="flex items-start justify-between">
            <div className="p-3 rounded-xl bg-danger/10 text-danger border border-danger/20">
              <AlertCircle size={24} />
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-lg text-text-secondary hover:text-text hover:bg-bg transition-colors cursor-pointer"
            >
              <X size={18} />
            </button>
          </div>

          <div>
            <h3 className="text-base font-bold text-text">Unable to Parse Document</h3>
            <p className="text-xs text-text-secondary mt-1">
              Text extraction for <strong className="text-text">{document.display_name}</strong> failed during processing. Would you like to retry parsing?
            </p>
          </div>

          <div className="p-3 rounded-xl bg-bg/50 border border-border/60 flex items-center gap-2.5 text-xs text-text-secondary">
            <FileText size={16} className="text-primary" />
            <span className="truncate">{document.original_filename}</span>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-border bg-bg hover:bg-bg-alt text-text text-xs font-semibold transition-colors cursor-pointer"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={() => {
                onConfirm(document.id);
                onClose();
              }}
              className="flex-1 inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all cursor-pointer"
            >
              <RefreshCw size={14} />
              <span>Retry Parsing</span>
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
