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
  CheckCircle2,
  Clock,
  AlertCircle,
  Sparkles,
} from "lucide-react";

export default function DocumentCard({
  document: doc,
  onPreview,
  onRename,
  onDownload,
  onDelete,
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

  // Icon & Theme based on file extension
  const ext = (doc.file_extension || "").toLowerCase();

  const getFormatDetails = () => {
    if (ext === "pdf") {
      return {
        icon: FileText,
        color: "text-rose-500",
        bg: "bg-rose-500/10",
        border: "border-rose-500/20",
        gradient: "from-rose-500/20 to-pink-500/5",
        label: "PDF Document",
      };
    } else if (ext === "md") {
      return {
        icon: FileText,
        color: "text-purple-500",
        bg: "bg-purple-500/10",
        border: "border-purple-500/20",
        gradient: "from-purple-500/20 to-indigo-500/5",
        label: "Markdown",
      };
    } else {
      return {
        icon: File,
        color: "text-blue-500",
        bg: "bg-blue-500/10",
        border: "border-blue-500/20",
        gradient: "from-blue-500/20 to-cyan-500/5",
        label: "Text File",
      };
    }
  };

  const fmt = getFormatDetails();
  const IconComponent = fmt.icon;

  // Status Badge details
  const getStatusBadge = () => {
    const status = (doc.status || "UPLOADED").toUpperCase();
    if (status === "READY") {
      return {
        label: "Ready for AI",
        icon: CheckCircle2,
        style: "bg-success/10 text-success border-success/20",
      };
    } else if (status === "PROCESSING") {
      return {
        label: "Processing",
        icon: Clock,
        style: "bg-purple-500/10 text-purple-500 border-purple-500/20 animate-pulse",
      };
    } else if (status === "FAILED") {
      return {
        label: "Failed",
        icon: AlertCircle,
        style: "bg-danger/10 text-danger border-danger/20",
      };
    } else {
      return {
        label: "Uploaded",
        icon: Clock,
        style: "bg-accent/10 text-accent border-accent/20",
      };
    }
  };

  const statusBadge = getStatusBadge();
  const StatusIcon = statusBadge.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 15, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -4, scale: 1.015 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-border/80 bg-bg/90 backdrop-blur-xs p-5 shadow-sm hover:shadow-xl hover:border-accent/30 transition-all duration-200"
    >
      {/* Subtle Top Gradient Accent on Hover */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${fmt.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-200`}
      />

      <div>
        {/* Top Header Row */}
        <div className="flex items-start justify-between gap-3 mb-4">
          {/* Layered Icon with Hover Micro-rotation */}
          <motion.div
            whileHover={{ rotate: 3, scale: 1.05 }}
            transition={{ duration: 0.15 }}
            className={`w-12 h-12 rounded-xl ${fmt.bg} ${fmt.border} border flex items-center justify-center ${fmt.color} shadow-xs shrink-0`}
          >
            <IconComponent size={24} />
          </motion.div>

          {/* Status Badge & 3-Dot Menu */}
          <div className="flex items-center gap-1.5">
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold ${statusBadge.style}`}
            >
              <StatusIcon size={11} />
              {statusBadge.label}
            </span>

            {/* Context Menu Dropdown */}
            <div ref={menuRef} className="relative">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsMenuOpen(!isMenuOpen);
                }}
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
                    className="absolute right-0 mt-1 w-40 rounded-xl border border-border bg-bg/95 backdrop-blur-md shadow-xl py-1 z-40 text-xs"
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
                      <span>Quick Preview</span>
                    </button>

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
                        onDownload(doc);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-bg-alt text-text font-medium transition-colors cursor-pointer"
                    >
                      <Download size={14} className="text-text-secondary" />
                      <span>Download</span>
                    </button>

                    <div className="h-px bg-border my-1" />

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
        </div>

        {/* Title */}
        <h3
          onClick={() => onPreview(doc)}
          className="text-sm font-bold text-text line-clamp-2 hover:text-accent cursor-pointer transition-colors leading-snug mb-2"
          title={doc.display_name}
        >
          {doc.display_name}
        </h3>
      </div>

      {/* Footer Info */}
      <div className="pt-3 mt-2 border-t border-border/50 flex items-center justify-between text-[11px] text-text-secondary">
        <div className="flex items-center gap-2 font-medium">
          <span className="uppercase font-bold tracking-wider text-text-secondary/80">
            {ext}
          </span>
          <span>•</span>
          <span>{formatSize(doc.file_size)}</span>
        </div>

        <span className="font-medium">{formatDate(doc.uploaded_at)}</span>
      </div>
    </motion.div>
  );
}
