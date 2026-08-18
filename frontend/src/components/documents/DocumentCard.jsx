import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import {
  FileText,
  File,
  MoreVertical,
  Download,
  Edit2,
  Trash2,
  Eye,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Sparkles,
  Layers,
  Bot,
} from "lucide-react";
import ProcessingBadge from "./ProcessingBadge";
import ProcessingTimeline from "./ProcessingTimeline";
import ProgressRing from "./ProgressRing";
import { useParsingStatus, useEmbeddingStatus, useVectorIndexStatus } from "../../hooks/useDocuments";

export default function DocumentCard({
  document: doc,
  isHovered = false,
  onPreview,
  onRename,
  onDownload,
  onDelete,
  onRetry,
  onExploreChunks,
}) {
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isTimelineExpanded, setIsTimelineExpanded] = useState(false);
  const menuRef = useRef(null);

  const handleUseInMentor = (e) => {
    e?.stopPropagation();
    navigate(`/mentor/knowledge?tab=rag&docId=${doc.id}`);
  };

  // Fetch parsed text status if ready
  const { data: parsedData } = useParsingStatus(doc.id, doc.status === "READY");

  // Fetch embedding status to update the pipeline timeline
  const { data: embeddingStatus } = useEmbeddingStatus(doc.id, doc.status === "READY");

  // Fetch FAISS vector status to update pipeline timeline
  const { data: vectorStatus } = useVectorIndexStatus(doc.id, doc.status === "READY");

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
      return {
        icon: FileText,
        color: "text-rose-600 dark:text-rose-400",
        bg: "bg-rose-50 dark:bg-rose-950/40",
        border: "border-rose-200 dark:border-rose-800/60",
        gradient: "from-rose-500 to-pink-500",
        label: "PDF Document",
      };
    } else if (ext === "md" || ext === "markdown") {
      return {
        icon: FileText,
        color: "text-purple-600 dark:text-purple-400",
        bg: "bg-purple-50 dark:bg-purple-950/40",
        border: "border-purple-200 dark:border-purple-800/60",
        gradient: "from-purple-500 to-indigo-500",
        label: "Markdown",
      };
    } else {
      return {
        icon: File,
        color: "text-blue-600 dark:text-blue-400",
        bg: "bg-blue-50 dark:bg-blue-950/40",
        border: "border-blue-200 dark:border-blue-800/60",
        gradient: "from-blue-500 to-cyan-500",
        label: "Text File",
      };
    }
  };

  const fmt = getFormatDetails();
  const IconComponent = fmt.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 15, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={`group relative flex flex-col justify-between rounded-2xl border p-5 transition-all duration-200 ${
        isHovered
          ? "border-indigo-500 dark:border-indigo-400 shadow-2xl bg-white dark:bg-slate-900 z-30"
          : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm"
      }`}
    >
      {/* Top Gradient Accent */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 rounded-t-2xl bg-gradient-to-r ${fmt.gradient} opacity-80 group-hover:opacity-100 transition-opacity duration-200`}
      />

      <div>
        {/* Top Header Row */}
        <div className="flex items-start justify-between gap-3 mb-3">
          {/* Layered Icon */}
          <div
            className={`w-11 h-11 rounded-xl ${fmt.bg} ${fmt.border} border flex items-center justify-center ${fmt.color} shadow-xs shrink-0`}
          >
            {doc.status === "PROCESSING" ? (
              <ProgressRing progress={65} size={36} strokeWidth={3} status="PROCESSING" />
            ) : (
              <IconComponent size={22} />
            )}
          </div>

          {/* Status Badge & 3-Dot Menu */}
          <div className="flex items-center gap-1.5 relative z-20">
            <ProcessingBadge status={doc.status} />

            {/* Context Menu Dropdown Container */}
            <div ref={menuRef} className="relative">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsMenuOpen(!isMenuOpen);
                }}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer transition-colors shadow-xs"
                title="Options"
              >
                <MoreVertical size={16} />
              </button>

              {/* Opaque 3-Dot Menu Dropdown (Prevents text bleeding) */}
              <AnimatePresence>
                {isMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 4 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 4 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-1 w-48 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-2xl py-1.5 z-50 text-xs divide-y divide-slate-100 dark:divide-slate-800"
                  >
                    <div className="py-0.5">
                      <button
                        type="button"
                        onClick={() => {
                          setIsMenuOpen(false);
                          onPreview(doc);
                        }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold transition-colors cursor-pointer"
                      >
                        <Eye size={14} className="text-indigo-500" />
                        <span>Details & Pipeline</span>
                      </button>

                      <button
                        type="button"
                        onClick={(e) => {
                          setIsMenuOpen(false);
                          handleUseInMentor(e);
                        }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 font-bold transition-colors cursor-pointer"
                      >
                        <Bot size={14} />
                        <span>Use in Mentor</span>
                      </button>

                      {onExploreChunks && (
                        <button
                          type="button"
                          onClick={() => {
                            setIsMenuOpen(false);
                            onExploreChunks(doc);
                          }}
                          className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 font-bold transition-colors cursor-pointer"
                        >
                          <Layers size={14} />
                          <span>AI Chunk Explorer</span>
                        </button>
                      )}

                      {doc.status === "FAILED" && onRetry && (
                        <button
                          type="button"
                          onClick={() => {
                            setIsMenuOpen(false);
                            onRetry(doc);
                          }}
                          className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-red-50 dark:hover:bg-red-950/40 text-red-600 dark:text-red-400 font-semibold transition-colors cursor-pointer"
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
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold transition-colors cursor-pointer"
                      >
                        <Edit2 size={14} className="text-slate-500" />
                        <span>Rename</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setIsMenuOpen(false);
                          onDownload(doc);
                        }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold transition-colors cursor-pointer"
                      >
                        <Download size={14} className="text-slate-500" />
                        <span>Download</span>
                      </button>
                    </div>

                    <div className="py-0.5">
                      <button
                        type="button"
                        onClick={() => {
                          setIsMenuOpen(false);
                          onDelete(doc);
                        }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-red-50 dark:hover:bg-red-950/40 text-red-600 dark:text-red-400 font-bold transition-colors cursor-pointer"
                      >
                        <Trash2 size={14} />
                        <span>Delete</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Title */}
        <h3
          onClick={() => onPreview(doc)}
          className="text-sm font-extrabold text-slate-900 dark:text-slate-100 line-clamp-2 hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer transition-colors leading-snug mb-1"
          title={doc.display_name}
        >
          {doc.display_name}
        </h3>

        {/* File Format details */}
        <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          {fmt.label} • {formatSize(doc.file_size)}
        </p>
      </div>

      {/* Expandable Pipeline Timeline */}
      <div className="mt-3">
        <button
          type="button"
          onClick={() => setIsTimelineExpanded(!isTimelineExpanded)}
          className="w-full flex items-center justify-between py-1.5 px-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-[10px] font-extrabold text-slate-700 dark:text-slate-300 uppercase tracking-wider transition-colors cursor-pointer"
        >
          <span className="flex items-center gap-1.5">
            <Sparkles size={11} className="text-indigo-500" />
            <span>AI Pipeline</span>
          </span>
          {isTimelineExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>

        <AnimatePresence>
          {isTimelineExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden pt-2"
            >
              <ProcessingTimeline
                documentStatus={doc.status}
                embeddingStatus={embeddingStatus}
                vectorStatus={vectorStatus}
                compact={true}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer Info & Action */}
      <div className="pt-3 mt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
        <span className="font-mono text-[10px] uppercase font-bold text-slate-600 dark:text-slate-400">
          .{ext}
        </span>
        {onExploreChunks && (doc.status === "READY" || doc.status === "PROCESSING") ? (
          <button
            type="button"
            onClick={() => onExploreChunks(doc)}
            className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors cursor-pointer"
          >
            <Layers size={12} />
            <span>Explore Chunks</span>
          </button>
        ) : (
          <span className="font-medium">{formatDate(doc.uploaded_at)}</span>
        )}
      </div>
    </motion.div>
  );
}
