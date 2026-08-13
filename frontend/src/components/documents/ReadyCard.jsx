import React from "react";
import { motion } from "motion/react";
import { CheckCircle2, ArrowRight, Sparkles, FileText, Scissors } from "lucide-react";

export default function ReadyCard({ document, parsedData, onOpenMetadata }) {
  if (!document || document.status !== "READY") return null;

  const charCount = parsedData?.char_count || 0;
  const wordEstimate = charCount ? Math.round(charCount / 5) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 backdrop-blur-md space-y-3"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
            <CheckCircle2 size={18} />
          </div>
          <div>
            <h4 className="text-xs font-bold text-text">Ready for AI Processing</h4>
            <p className="text-[11px] text-text-secondary">
              Successfully converted into clean structured text
            </p>
          </div>
        </div>

        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
          <Sparkles size={10} />
          Text Extracted
        </span>
      </div>

      {/* Extracted Text Quick Metrics */}
      <div className="grid grid-cols-2 gap-2 text-[11px] bg-surface/50 p-2.5 rounded-lg border border-border/40">
        <div>
          <span className="text-text-secondary block text-[10px]">Text Length</span>
          <span className="font-semibold text-text">
            {charCount > 0 ? `${charCount.toLocaleString()} chars` : "Text Ready"}
          </span>
        </div>
        <div>
          <span className="text-text-secondary block text-[10px]">Estimated Words</span>
          <span className="font-semibold text-text">
            {wordEstimate ? `~${wordEstimate.toLocaleString()} words` : "Parsed"}
          </span>
        </div>
      </div>

      {/* Next Pipeline Step Banner */}
      <div className="flex items-center justify-between pt-1 border-t border-emerald-500/20 text-[11px]">
        <div className="flex items-center gap-1.5 text-text-secondary">
          <Scissors size={12} className="text-primary" />
          <span>Next: <strong className="text-text">Chunk Generation</strong></span>
        </div>
        {onOpenMetadata && (
          <button
            type="button"
            onClick={onOpenMetadata}
            className="inline-flex items-center gap-1 text-primary hover:underline font-semibold text-[11px] cursor-pointer"
          >
            <span>Details</span>
            <ArrowRight size={12} />
          </button>
        )}
      </div>
    </motion.div>
  );
}
