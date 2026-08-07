import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FileText,
  File,
  MoreVertical,
  Download,
  Edit2,
  Trash2,
  Eye,
  RefreshCw,
  Layers,
} from "lucide-react";
import ProcessingBadge from "./ProcessingBadge";

export default function DocumentListItem({
  document: doc,
  onPreview,
  onRename,
  onDownload,
  onDelete,
  onRetry,
  onExploreChunks,
}) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const formatSize = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const formatDate = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const ext = (doc.file_extension || "").toLowerCase();

  const getFormatDetails = () => {
    if (ext === "pdf") {
      return { icon: FileText, color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/20" };
    } else if (ext === "md" || ext === "markdown") {
      return { icon: FileText, color: "text-purple-500", bg: "bg-purple-500/10", border: "border-purple-500/20" };
    } else {
      return { icon: File, color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20" };
    }
  };

  const fmt = getFormatDetails();
  const IconComponent = fmt.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      whileHover={{ x: 2 }}
      transition={{ duration: 0.2 }}
      className="group relative flex items-center justify-between gap-4 rounded-xl border border-border/80 bg-surface/90 p-3.5 shadow-2xs hover:shadow-md hover:border-primary/30 transition-all duration-150"
    >
      {/* Left: Icon & Title */}
      <div className="flex items-center gap-3.5 min-w-0 flex-1">
        <div className={`w-10 h-10 rounded-lg ${fmt.bg} ${fmt.border} border flex items-center justify-center ${fmt.color} shrink-0`}>
          <IconComponent size={20} />
        </div>

        <div className="min-w-0 flex-1">
          <h4
            onClick={() => onPreview(doc)}
            className="text-xs sm:text-sm font-bold text-text truncate hover:text-primary cursor-pointer transition-colors"
            title={doc.display_name}
          >
            {doc.display_name}
          </h4>
          <p className="text-[11px] text-text-secondary truncate mt-0.5">
            {doc.original_filename}
          </p>
        </div>
      </div>

      {/* Center: Metadata */}
      <div className="hidden md:flex items-center gap-6 text-xs text-text-secondary">
        <span className="uppercase font-bold text-[10px] tracking-wider w-10 text-center">
          {ext}
        </span>
        <span className="w-16 text-right font-medium">{formatSize(doc.file_size)}</span>
        <span className="w-24 text-right font-medium">{formatDate(doc.uploaded_at)}</span>
      </div>

      {/* Right: Status & Actions */}
      <div className="flex items-center gap-2">
        {onExploreChunks && (doc.status === "READY" || doc.status === "PROCESSING") && (
          <button
            type="button"
            onClick={() => onExploreChunks(doc)}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900 text-xs font-bold transition-colors cursor-pointer"
          >
            <Layers size={13} />
            <span>Chunks</span>
          </button>
        )}
        <div className="hidden sm:block">
          <ProcessingBadge status={doc.status} />
        </div>

        <button
          type="button"
          onClick={() => onPreview(doc)}
          className="p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text transition-colors cursor-pointer"
          title="Quick Details"
        >
          <Eye size={16} />
        </button>

        <button
          type="button"
          onClick={() => onDownload(doc)}
          className="p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text transition-colors cursor-pointer"
          title="Download"
        >
          <Download size={16} />
        </button>

        {/* 3-Dot Menu */}
        <div ref={menuRef} className="relative">
          <button
            type="button"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-colors"
            title="Options"
          >
            <MoreVertical size={16} />
          </button>

          <AnimatePresence>
            {isMenuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.12 }}
                className="absolute right-0 mt-1 w-44 rounded-xl border border-border bg-surface/95 backdrop-blur-xl shadow-xl py-1 z-40 text-xs"
              >
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onPreview(doc);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-bg-alt text-text font-medium transition-colors cursor-pointer"
                >
                  <Eye size={14} className="text-text-secondary" />
                  <span>Details & Pipeline</span>
                </button>

                {doc.status === "FAILED" && onRetry && (
                  <button
                    type="button"
                    onClick={() => {
                      setIsMenuOpen(false);
                      onRetry(doc);
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-primary/10 text-primary font-medium transition-colors cursor-pointer"
                  >
                    <RefreshCw size={14} />
                    <span>Retry Parsing</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onRename(doc);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-bg-alt text-text font-medium transition-colors cursor-pointer"
                >
                  <Edit2 size={14} className="text-text-secondary" />
                  <span>Rename</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onDelete(doc);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-danger/10 text-danger font-medium transition-colors cursor-pointer"
                >
                  <Trash2 size={14} />
                  <span>Delete</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
