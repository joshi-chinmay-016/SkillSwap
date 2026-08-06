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
    <div className="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-b from-bg to-bg-alt p-6 md:p-8 shadow-lg">
      {/* Background Animated Blobs (Low GPU cost CSS/motion) */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <motion.div
          animate={{
            x: [0, 30, 0],
            y: [0, -20, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -top-16 -left-16 w-72 h-72 rounded-full bg-accent/15 blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, -25, 0],
            y: [0, 25, 0],
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 22,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -bottom-16 -right-16 w-80 h-80 rounded-full bg-purple-500/10 blur-3xl"
        />
        <div className="absolute inset-0 bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:24px_24px] opacity-[0.03]" />
      </div>

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="max-w-2xl">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/20 bg-accent/10 text-accent text-xs font-semibold mb-4"
          >
            <Sparkles size={14} className="animate-pulse" />
            <span>AI Knowledge Engine</span>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.05 }}
            className="text-2xl md:text-3xl font-extrabold tracking-tight text-text"
          >
            Your AI Knowledge Library
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.1 }}
            className="mt-2 text-sm text-text-secondary leading-relaxed"
          >
            Store notes, books, and PDFs. These documents will become automatically searchable and ready for retrieval by your AI Mentor.
          </motion.p>

          {/* Stats Bar */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.15 }}
            className="mt-5 flex flex-wrap items-center gap-4 text-xs"
          >
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg/80 border border-border/70 backdrop-blur-xs">
              <Layers size={14} className="text-accent" />
              <span className="text-text-secondary font-medium">Documents:</span>
              <span className="font-bold text-text">{totalDocuments}</span>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg/80 border border-border/70 backdrop-blur-xs">
              <HardDrive size={14} className="text-purple-500" />
              <span className="text-text-secondary font-medium">Storage Used:</span>
              <span className="font-bold text-text">{formatBytes(totalBytes)}</span>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg/80 border border-border/70 backdrop-blur-xs">
              <ShieldCheck size={14} className={isHealthy ? "text-success" : "text-warning"} />
              <span className="text-text-secondary font-medium">Storage System:</span>
              <span className={`font-semibold ${isHealthy ? "text-success" : "text-warning"}`}>
                {isHealthy ? "Healthy" : "Degraded"}
              </span>
            </div>
          </motion.div>
        </div>

        {/* Hero CTA Button */}
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
            className="w-full md:w-auto inline-flex items-center justify-center gap-2.5 px-5 py-3 rounded-xl bg-accent text-white font-semibold text-sm shadow-md shadow-accent/20 hover:bg-accent-hover cursor-pointer transition-all duration-150"
          >
            <UploadCloud size={18} />
            <span>Upload Document</span>
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
}
