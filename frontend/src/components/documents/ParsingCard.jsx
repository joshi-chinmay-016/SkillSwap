import React from "react";
import { motion } from "motion/react";
import { Loader2, FileText, Cpu, Sparkles } from "lucide-react";
import ProgressRing from "./ProgressRing";

export default function ParsingCard({ document }) {
  if (!document) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-4 rounded-xl border border-primary/30 bg-primary/5 backdrop-blur-md space-y-3 relative overflow-hidden"
    >
      {/* Animated Subtle Shimmer Bar */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent"
        animate={{ x: ["-100%", "100%"] }}
        transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ProgressRing progress={65} size={40} strokeWidth={3.5} status="PROCESSING" />
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-bold text-text truncate max-w-[200px]">
                {document.display_name}
              </h4>
              <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20 animate-pulse">
                Processing
              </span>
            </div>
            <p className="text-[11px] text-text-secondary mt-0.5 flex items-center gap-1">
              <Cpu size={12} className="text-primary animate-spin" />
              <span>Extracting text & validating structure...</span>
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[10px] text-text-secondary block">Parser Engine</span>
          <span className="text-xs font-bold text-primary font-mono">v1.0 (PyMuPDF)</span>
        </div>
      </div>
    </motion.div>
  );
}
