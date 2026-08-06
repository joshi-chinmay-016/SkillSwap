import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { AlertTriangle, X, Trash2 } from "lucide-react";

export default function DeleteDialog({ document: doc, isOpen, onClose, onConfirm }) {
  if (!isOpen || !doc) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/40 backdrop-blur-xs"
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ type: "spring", stiffness: 350, damping: 25 }}
          className="relative z-10 w-full max-w-md overflow-hidden rounded-2xl border border-border bg-bg p-6 shadow-2xl"
        >
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-danger/10 text-danger border border-danger/20">
                <AlertTriangle size={22} />
              </div>
              <div>
                <h3 className="text-base font-bold text-text">Delete Document</h3>
                <p className="text-xs text-text-secondary mt-0.5">This action cannot be undone.</p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text transition-colors cursor-pointer"
            >
              <X size={16} />
            </button>
          </div>

          <div className="p-3.5 rounded-xl bg-bg-alt border border-border/80 my-4 text-xs">
            <p className="text-text-secondary font-medium mb-1">Document to be deleted:</p>
            <p className="font-bold text-text truncate">{doc.display_name}</p>
            <p className="text-[11px] text-text-secondary/70 truncate">{doc.original_filename}</p>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-bg-alt border border-border text-xs font-semibold text-text hover:bg-bg transition-colors cursor-pointer"
            >
              Cancel
            </button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="button"
              onClick={() => {
                onConfirm(doc.id);
                onClose();
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-danger text-white font-semibold text-xs hover:bg-danger/90 transition-all cursor-pointer shadow-xs"
            >
              <Trash2 size={14} />
              <span>Delete Document</span>
            </motion.button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
