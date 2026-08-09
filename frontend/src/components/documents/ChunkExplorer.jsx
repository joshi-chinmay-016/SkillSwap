import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  X,
  Search,
  Layers,
  Sparkles,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Database,
  CheckCircle2,
  Cpu,
} from "lucide-react";
import { useChunks, useChunkMetadata, useRechunkDocument, useEmbeddingStatus } from "../../hooks/useDocuments";
import ChunkStatistics from "./ChunkStatistics";
import ChunkGraph from "./ChunkGraph";
import ChunkCard from "./ChunkCard";
import ChunkDrawer from "./ChunkDrawer";
import EmbeddingStatus from "./EmbeddingStatus";
import EmbeddingVisualization from "./EmbeddingVisualization";
import EmbeddingDetailsDrawer from "./EmbeddingDetailsDrawer";
import VectorIndexStatus from "./VectorIndexStatus";
import VectorIndexVisualization from "./VectorIndexVisualization";

export default function ChunkExplorer({ document, onClose }) {
  if (!document) return null;

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSection, setSelectedSection] = useState("all");
  const [selectedChunk, setSelectedChunk] = useState(null);
  const [embeddingDrawerChunk, setEmbeddingDrawerChunk] = useState(null);
  const [showEmbeddingPanel, setShowEmbeddingPanel] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Queries
  const { data: chunksData, isLoading: isChunksLoading } = useChunks({
    documentId: document.id,
    page,
    page_size: pageSize,
  });

  const { data: metadata, isLoading: isMetadataLoading } = useChunkMetadata(document.id);
  const { data: embeddingStatus } = useEmbeddingStatus(document.id);
  const rechunkMutation = useRechunkDocument();

  const chunks = chunksData?.chunks || [];
  const total = chunksData?.total || 0;

  // Extract unique sections for filtering
  const sections = useMemo(() => {
    const set = new Set();
    chunks.forEach((c) => {
      if (c.section) set.add(c.section);
    });
    return ["all", ...Array.from(set)];
  }, [chunks]);

  // Filtered chunks
  const filteredChunks = useMemo(() => {
    return chunks.filter((chunk) => {
      const matchesSearch =
        !searchQuery ||
        chunk.chunk_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        `chunk #${chunk.chunk_index}`.includes(searchQuery.toLowerCase());
      const matchesSection = selectedSection === "all" || chunk.section === selectedSection;
      return matchesSearch && matchesSection;
    });
  }, [chunks, searchQuery, selectedSection]);

  const handleRechunk = () => {
    rechunkMutation.mutate(document.id);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center p-4 sm:p-6">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/70 backdrop-blur-sm"
        />

        {/* Modal Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 250 }}
          className="relative z-10 w-full max-w-5xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col max-h-[90vh] overflow-hidden"
        >
          {/* Top Header */}
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/90 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-600/10 dark:bg-indigo-400/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-black">
                <Layers size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-black text-slate-900 dark:text-white">
                    AI Knowledge Chunk Explorer
                  </h2>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 text-[10px] font-extrabold border border-emerald-300 dark:border-emerald-800">
                    READY
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-semibold truncate max-w-md">
                  {document.display_name} ({document.original_filename})
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Embedding Panel Toggle */}
              <button
                onClick={() => setShowEmbeddingPanel((v) => !v)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                  showEmbeddingPanel
                    ? "bg-indigo-600 text-white"
                    : "bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-900"
                }`}
              >
                <Cpu size={13} />
                <span>Embeddings</span>
              </button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleRechunk}
                disabled={rechunkMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors cursor-pointer"
              >
                <RefreshCw size={13} className={rechunkMutation.isPending ? "animate-spin" : ""} />
                <span>{rechunkMutation.isPending ? "Rechunking..." : "Re-chunk Document"}</span>
              </motion.button>

              <button
                onClick={onClose}
                className="p-1.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Main Scrollable Area */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {/* Statistics Row */}
            <ChunkStatistics metadata={metadata} isLoading={isMetadataLoading} />

            {/* Embedding & Vector Index Panel (toggled) */}
            <AnimatePresence>
              {showEmbeddingPanel && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.25 }}
                  className="overflow-hidden space-y-4"
                >
                  <EmbeddingStatus documentId={document.id} documentStatus={document.status} />
                  <VectorIndexStatus documentId={document.id} />
                  <VectorIndexVisualization
                    vectorCount={embeddingStatus?.ready || 0}
                    dimension={768}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Node Flow Diagram */}
            <ChunkGraph
              totalChunks={metadata?.total_chunks || chunks.length}
              documentName={document.display_name}
            />

            {/* Search & Filter Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="relative flex-1 min-w-[200px]">
                <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search chunk text or #index..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {sections.length > 1 && (
                <div className="flex items-center gap-1.5 overflow-x-auto py-1">
                  <span className="text-[11px] font-bold text-slate-400">Section:</span>
                  {sections.map((sec) => (
                    <button
                      key={sec}
                      onClick={() => setSelectedSection(sec)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold capitalize transition-colors cursor-pointer ${
                        selectedSection === sec
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                      }`}
                    >
                      {sec}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Chunk Cards Grid */}
            {isChunksLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 py-4">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="h-28 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse border border-slate-200 dark:border-slate-700"
                  />
                ))}
              </div>
            ) : filteredChunks.length === 0 ? (
              <div className="text-center py-10 bg-slate-50 dark:bg-slate-950/40 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
                <Layers className="mx-auto text-slate-400 mb-2" size={32} />
                <p className="text-xs font-extrabold text-slate-600 dark:text-slate-400">
                  No chunks match your search criteria.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 py-2">
                {filteredChunks.map((chunk) => (
                  <ChunkCard
                    key={chunk.id || chunk.chunk_index}
                    chunk={chunk}
                    isSelected={selectedChunk?.chunk_index === chunk.chunk_index}
                    onClick={() => {
                      setSelectedChunk(chunk);
                      setEmbeddingDrawerChunk(null);
                    }}
                    onViewEmbedding={(e) => {
                      e.stopPropagation();
                      setEmbeddingDrawerChunk(chunk);
                      setSelectedChunk(null);
                    }}
                  />
                ))}
              </div>
            )}

            {/* Pagination Controls */}
            {total > pageSize && (
              <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-800 text-xs font-semibold">
                <span className="text-slate-500">
                  Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} chunks
                </span>

                <div className="flex items-center gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="font-bold text-slate-900 dark:text-white">
                    Page {page} of {Math.ceil(total / pageSize)}
                  </span>
                  <button
                    disabled={page * pageSize >= total}
                    onClick={() => setPage((p) => p + 1)}
                    className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Single Chunk Detail Drawer overlay */}
          <ChunkDrawer chunk={selectedChunk} onClose={() => setSelectedChunk(null)} />

          {/* Embedding Details Drawer overlay */}
          <EmbeddingDetailsDrawer
            chunk={embeddingDrawerChunk}
            embeddingMeta={embeddingStatus}
            onClose={() => setEmbeddingDrawerChunk(null)}
          />
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
