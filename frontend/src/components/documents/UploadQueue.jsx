import React from "react";
import { motion, AnimatePresence } from "motion/react";
import UploadProgressCard from "./UploadProgressCard";

export default function UploadQueue({ queue = [], onDismissItem, onRetryItem }) {
  if (!queue || queue.length === 0) return null;

  const activeCount = queue.filter((item) => item.status === "uploading").length;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="my-4 space-y-2"
    >
      <div className="flex items-center justify-between text-xs font-semibold text-text-secondary px-1">
        <span>Upload Queue ({queue.length})</span>
        {activeCount > 0 && <span className="text-accent animate-pulse">{activeCount} uploading...</span>}
      </div>

      <div className="space-y-2">
        <AnimatePresence mode="popLayout">
          {queue.map((item) => (
            <UploadProgressCard
              key={item.id}
              item={item}
              onCancel={onDismissItem}
              onRetry={onRetryItem}
            />
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
