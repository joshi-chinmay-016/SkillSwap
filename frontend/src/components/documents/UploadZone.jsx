import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { UploadCloud, FileText, File, AlertCircle } from "lucide-react";

export default function UploadZone({ onFilesSelected, maxSizeBytes = 26214400 }) {
  const [isDragging, setIsDragging] = useState(false);
  const [hasDropped, setHasDropped] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setHasDropped(true);

    setTimeout(() => setHasDropped(false), 800);

    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0 && onFilesSelected) {
      onFilesSelected(files);
    }
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0 && onFilesSelected) {
      onFilesSelected(files);
    }
    // Reset file input so re-selecting same file works
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatSize = (bytes) => (bytes / (1024 * 1024)).toFixed(0) + " MB";

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="relative"
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
        onChange={handleFileChange}
        className="hidden"
        id="document-file-input"
      />

      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        whileHover={{ scale: 1.005, y: -2 }}
        whileTap={{ scale: 0.995 }}
        className={`
          relative overflow-hidden rounded-2xl border-2 border-dashed p-8 md:p-10
          text-center cursor-pointer transition-all duration-200 select-none
          ${
            isDragging
              ? "border-accent bg-accent/10 shadow-xl shadow-accent/10 scale-[1.01]"
              : "border-border hover:border-accent/60 bg-bg/60 hover:bg-bg/90 shadow-sm hover:shadow-md"
          }
        `}
      >
        {/* Drop Ripple Animation */}
        <AnimatePresence>
          {hasDropped && (
            <motion.div
              initial={{ scale: 0, opacity: 0.8 }}
              animate={{ scale: 3, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.7, ease: "easeOut" }}
              className="absolute inset-0 m-auto w-32 h-32 rounded-full bg-accent/20 pointer-events-none"
            />
          )}
        </AnimatePresence>

        {/* Outer Glow on Drag */}
        {isDragging && (
          <div className="absolute inset-0 bg-gradient-to-r from-accent/5 via-purple-500/5 to-accent/5 pointer-events-none animate-pulse" />
        )}

        <div className="relative z-10 flex flex-col items-center justify-center gap-3">
          {/* Animated Upload Icon */}
          <motion.div
            animate={isDragging ? { y: [-4, 4, -4], scale: 1.1 } : { y: 0, scale: 1 }}
            transition={{ duration: 1.5, repeat: isDragging ? Infinity : 0 }}
            className={`
              w-16 h-16 rounded-2xl flex items-center justify-center transition-colors duration-200
              ${isDragging ? "bg-accent text-white shadow-lg shadow-accent/30" : "bg-accent/10 text-accent"}
            `}
          >
            <UploadCloud size={32} />
          </motion.div>

          {/* Heading */}
          <h3 className="text-base md:text-lg font-bold text-text mt-1">
            {isDragging ? "Drop your files here" : "Drag & drop PDFs, Notes, or Books here"}
          </h3>

          {/* Subtext */}
          <p className="text-xs text-text-secondary max-w-md leading-relaxed">
            or <span className="text-accent font-semibold underline underline-offset-2">browse files</span> from your computer. Supports single or batch uploads.
          </p>

          {/* Format Pills */}
          <div className="flex items-center justify-center gap-2 mt-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-rose-500/10 text-rose-500 border border-rose-500/20 text-[11px] font-semibold">
              <FileText size={12} />
              PDF
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-500 border border-blue-500/20 text-[11px] font-semibold">
              <File size={12} />
              TXT
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-500/10 text-purple-500 border border-purple-500/20 text-[11px] font-semibold">
              <FileText size={12} />
              Markdown (.md)
            </span>
            <span className="text-[11px] text-text-secondary font-medium ml-1">
              Max {formatSize(maxSizeBytes)}
            </span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
