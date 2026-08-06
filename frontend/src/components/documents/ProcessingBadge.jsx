import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { Check, Loader2, AlertTriangle, FileText } from "lucide-react";

export default function ProcessingBadge({ status = "UPLOADED" }) {
  const getBadgeConfig = () => {
    switch (status) {
      case "PROCESSING":
        return {
          bg: "bg-indigo-500/15 border-indigo-500/30 text-indigo-700 dark:text-indigo-400 font-bold",
          dotColor: "bg-indigo-500",
          label: "Parsing...",
          animateSpin: true,
        };
      case "READY":
        return {
          bg: "bg-emerald-500/15 border-emerald-500/30 text-emerald-700 dark:text-emerald-400 font-bold",
          dotColor: "bg-emerald-500",
          label: "Parsed",
          animateSpin: false,
        };
      case "FAILED":
        return {
          bg: "bg-red-500/15 border-red-500/30 text-red-700 dark:text-red-400 font-bold",
          dotColor: "bg-red-500",
          label: "Failed",
          animateSpin: false,
        };
      case "UPLOADED":
      default:
        return {
          bg: "bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400 font-bold",
          dotColor: "bg-amber-500",
          label: "Uploaded",
          animateSpin: false,
        };
    }
  };

  const config = getBadgeConfig();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{ duration: 0.2 }}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-bold tracking-wide shadow-xs ${config.bg}`}
      >
        {config.animateSpin ? (
          <Loader2 size={12} className="animate-spin text-indigo-600 dark:text-indigo-400" />
        ) : status === "READY" ? (
          <Check size={12} strokeWidth={3} className="text-emerald-600 dark:text-emerald-400" />
        ) : status === "FAILED" ? (
          <AlertTriangle size={12} className="text-red-600 dark:text-red-400" />
        ) : (
          <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor} animate-pulse`} />
        )}
        <span>{config.label}</span>
      </motion.div>
    </AnimatePresence>
  );
}
