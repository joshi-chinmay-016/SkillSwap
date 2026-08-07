import React from "react";
import { motion } from "motion/react";
import { Sparkles, HardDrive, ShieldCheck, UploadCloud, Layers } from "lucide-react";

export default function Hero({ totalDocuments = 0, totalBytes = 0, isHealthy = true, onQuickUpload }) {
  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 md:p-8 shadow-xl text-slate-900 dark:text-slate-100">
      {/* Background Animated Particles & Ambient Glow */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Floating Particles */}
        <motion.div
          animate={{
            y: [0, -25, 0],
            opacity: [0.3, 0.7, 0.3],
          }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/4 left-1/5 w-2 h-2 rounded-full bg-indigo-500/40 blur-xs"
        />
        <motion.div
          animate={{
            y: [0, 35, 0],
            opacity: [0.2, 0.6, 0.2],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="absolute top-2/3 right-1/4 w-3 h-3 rounded-full bg-purple-500/40 blur-xs"
        />

        {/* Ambient Glows */}
        <motion.div
          animate={{
            x: [0, 40, 0],
            y: [0, -30, 0],
            scale: [1, 1.15, 1],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -top-20 -left-20 w-80 h-80 rounded-full bg-indigo-500/10 dark:bg-indigo-500/20 blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, -30, 0],
            y: [0, 30, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 22,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -bottom-20 -right-20 w-96 h-96 rounded-full bg-emerald-500/10 dark:bg-emerald-500/15 blur-3xl"
        />
        <div className="absolute inset-0 bg-[radial-gradient(#6366f1_1px,transparent_1px)] [background-size:24px_24px] opacity-[0.03]" />
      </div>

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="max-w-2xl">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 text-xs font-extrabold mb-3 shadow-xs"
          >
            <Sparkles size={14} className="animate-pulse text-indigo-600 dark:text-indigo-400" />
            <span>AI Knowledge Engine Pipeline</span>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.05 }}
            className="text-2xl md:text-3xl font-black tracking-tight text-slate-900 dark:text-white"
          >
            AI Knowledge Library
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.1 }}
            className="mt-2 text-sm font-semibold text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl"
          >
            Your learning resources are transformed into intelligent knowledge blocks that power your personal AI Mentor.
          </motion.p>

          {/* Stats Bar */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.15 }}
            className="mt-5 flex flex-wrap items-center gap-3 text-xs"
          >
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-xs">
              <Layers size={14} className="text-indigo-600 dark:text-indigo-400" />
              <span className="text-slate-600 dark:text-slate-400 font-bold">Documents:</span>
              <span className="font-extrabold text-slate-900 dark:text-white">{totalDocuments}</span>
            </div>

            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-xs">
              <HardDrive size={14} className="text-purple-600 dark:text-purple-400" />
              <span className="text-slate-600 dark:text-slate-400 font-bold">Storage:</span>
              <span className="font-extrabold text-slate-900 dark:text-white">{formatBytes(totalBytes)}</span>
            </div>

            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-xs">
              <ShieldCheck size={14} className={isHealthy ? "text-emerald-600 dark:text-emerald-400" : "text-amber-500"} />
              <span className="text-slate-600 dark:text-slate-400 font-bold">Pipeline:</span>
              <span className={`font-extrabold ${isHealthy ? "text-emerald-600 dark:text-emerald-400" : "text-amber-500"}`}>
                {isHealthy ? "Active" : "Degraded"}
              </span>
            </div>
          </motion.div>
        </div>

        {/* High Contrast Upload Document CTA Button */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.35, delay: 0.2 }}
          className="shrink-0"
        >
          <motion.button
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={onQuickUpload}
            className="w-full md:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-indigo-600 dark:bg-indigo-500 hover:bg-indigo-700 dark:hover:bg-indigo-600 text-white font-extrabold text-sm shadow-xl shadow-indigo-600/30 hover:shadow-indigo-600/40 cursor-pointer transition-all duration-150 border border-indigo-500/50"
          >
            <UploadCloud size={20} className="text-white shrink-0" />
            <span className="text-white font-black tracking-wide">Upload Document</span>
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
}
