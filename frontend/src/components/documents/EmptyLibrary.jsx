import React from "react";
import { motion } from "motion/react";
import { FolderOpen, UploadCloud, Sparkles } from "lucide-react";

export default function EmptyLibrary({ onUploadClick }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col items-center justify-center text-center p-12 md:p-16 rounded-2xl border border-dashed border-border bg-bg/40 my-8 select-none"
    >
      {/* Floating 3D Folder Illustration */}
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="relative mb-6"
      >
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-tr from-accent/20 via-purple-500/15 to-accent/10 flex items-center justify-center text-accent shadow-xl shadow-accent/10 border border-accent/20">
          <FolderOpen size={48} />
        </div>
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.9, 0.5] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-2 -right-2 p-1.5 rounded-full bg-accent text-white shadow-md"
        >
          <Sparkles size={14} />
        </motion.div>
      </motion.div>

      {/* Heading */}
      <h3 className="text-xl font-bold text-text mb-2">
        Your AI Knowledge Library is Empty
      </h3>

      {/* Subtext */}
      <p className="text-xs md:text-sm text-text-secondary max-w-md leading-relaxed mb-6">
        Upload your first learning resource (PDF, TXT, or Markdown). Files uploaded here will automatically become part of your personal AI knowledge base.
      </p>

      {/* Action Button */}
      <motion.button
        whileHover={{ scale: 1.04, y: -2 }}
        whileTap={{ scale: 0.97 }}
        onClick={onUploadClick}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-accent text-white font-semibold text-xs shadow-md shadow-accent/20 hover:bg-accent-hover cursor-pointer transition-colors"
      >
        <UploadCloud size={16} />
        <span>Upload First Document</span>
      </motion.button>
    </motion.div>
  );
}
