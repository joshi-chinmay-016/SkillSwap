import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Search,
  SlidersHorizontal,
  FileText,
  Clock,
  Zap,
  Database,
  Layers,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  X,
  AlertTriangle,
  Info,
  Compass,
  ArrowRight,
} from "lucide-react";
import { useRetrievalSearch } from "../../hooks/useRetrieval";
import { useToast } from "../common/Toast";

export default function RetrievalStudio({ documents = [], onClose }) {
  const toast = useToast();
  const [query, setQuery] = useState("");
  const [selectedDocId, setSelectedDocId] = useState("");
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.0);
  const [expandedChunkId, setExpandedChunkId] = useState(null);
  const [copiedChunkId, setCopiedChunkId] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const searchMutation = useRetrievalSearch();

  const handleSearch = (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) {
      toast.warning("Please enter a search query.", "Empty Query");
      return;
    }
    searchMutation.mutate({
      query: query.trim(),
      top_k: topK,
      similarity_threshold: threshold,
      document_id: selectedDocId || null,
    });
  };

  const handleCopy = (text, chunkId) => {
    navigator.clipboard.writeText(text);
    setCopiedChunkId(chunkId);
    toast.success("Chunk text copied to clipboard.");
    setTimeout(() => setCopiedChunkId(null), 2000);
  };

  const resultsData = searchMutation.data;
  const isPending = searchMutation.isPending;
  const isError = searchMutation.isError;
  const errorObj = searchMutation.error;

  return (
    <div className="bg-bg border border-border rounded-2xl shadow-xl overflow-hidden mb-8 transition-colors duration-200">
      {/* Header */}
      <div className="px-6 py-5 bg-bg-alt/50 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center border border-accent/20">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-base font-bold text-text flex items-center gap-2">
              Semantic Knowledge Retrieval Studio
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-accent/10 text-accent border border-accent/20">
                Day 71 Part A+B
              </span>
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Query your indexed documents using 3072-dimensional Gemini embeddings & FAISS exact search.
            </p>
          </div>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-colors"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Search Input Bar */}
      <div className="p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative flex items-center">
            <div className="absolute left-4 text-text-secondary pointer-events-none">
              <Search size={20} />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What is dependency injection in FastAPI? or Describe React hooks..."
              className="w-full pl-12 pr-28 py-3.5 bg-bg border border-border rounded-xl text-sm font-medium text-text placeholder-text-secondary/60 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all shadow-inner"
            />
            <div className="absolute right-2 flex items-center gap-2">
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="p-1.5 text-text-secondary hover:text-text rounded-md hover:bg-bg-alt cursor-pointer"
                >
                  <X size={16} />
                </button>
              )}
              <button
                type="submit"
                disabled={isPending || !query.trim()}
                className="px-4 py-2 bg-accent text-white rounded-lg text-xs font-semibold hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-all flex items-center gap-1.5 shadow-sm"
              >
                {isPending ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <span>Retrieve</span>
                    <ArrowRight size={14} />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 text-xs pt-1">
            <div className="flex flex-wrap items-center gap-3">
              {/* Scope selector */}
              <div className="flex items-center gap-2 bg-bg-alt px-3 py-1.5 rounded-lg border border-border">
                <FileText size={14} className="text-text-secondary" />
                <span className="text-text-secondary font-medium">Scope:</span>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="bg-transparent text-text font-semibold focus:outline-none cursor-pointer"
                >
                  <option value="">All Indexed Documents</option>
                  {documents
                    .filter((d) => d.status === "READY")
                    .map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.original_filename}
                      </option>
                    ))}
                </select>
              </div>

              {/* Top K selector */}
              <div className="flex items-center gap-2 bg-bg-alt px-3 py-1.5 rounded-lg border border-border">
                <Layers size={14} className="text-text-secondary" />
                <span className="text-text-secondary font-medium">Top K:</span>
                <select
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="bg-transparent text-text font-semibold focus:outline-none cursor-pointer"
                >
                  <option value={3}>3 Chunks</option>
                  <option value={5}>5 Chunks</option>
                  <option value={10}>10 Chunks</option>
                  <option value={20}>20 Chunks</option>
                </select>
              </div>

              {/* Advanced Toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1.5 text-text-secondary hover:text-accent font-semibold px-2 py-1 rounded hover:bg-bg-alt transition-colors"
              >
                <SlidersHorizontal size={14} />
                <span>Threshold ({threshold.toFixed(2)})</span>
                {showAdvanced ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>
            </div>

            <div className="text-[11px] text-text-secondary font-medium">
              Model: <span className="font-semibold text-text">gemini-embedding-001</span> (3072 dims)
            </div>
          </div>

          {/* Advanced Controls Panel */}
          {showAdvanced && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="p-4 bg-bg-alt/70 border border-border rounded-xl text-xs space-y-3"
            >
              <div className="flex items-center justify-between">
                <label className="font-semibold text-text flex items-center gap-2">
                  <span>Minimum Similarity Score Threshold:</span>
                  <span className="px-2 py-0.5 bg-accent/10 text-accent rounded font-mono font-bold">
                    {threshold.toFixed(2)}
                  </span>
                </label>
                <span className="text-[11px] text-text-secondary">
                  (0.00 = no threshold, 1.00 = exact match)
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="0.9"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full accent-accent cursor-pointer"
              />
            </motion.div>
          )}
        </form>

        {/* Timing Instrumentation Panel */}
        {resultsData && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-3 bg-bg-alt/40 border border-border rounded-xl flex flex-wrap items-center justify-between gap-4 text-xs"
          >
            <div className="flex items-center gap-2 text-text font-semibold">
              <Zap size={14} className="text-accent" />
              <span>Total Pipeline: {resultsData.query_duration_ms} ms</span>
            </div>

            <div className="flex items-center gap-4 text-text-secondary text-[11px]">
              <span className="flex items-center gap-1">
                <Clock size={12} className="text-blue-500" />
                Query Embed: <strong className="text-text">{resultsData.embedding_ms} ms</strong>
              </span>
              <span className="flex items-center gap-1">
                <Compass size={12} className="text-emerald-500" />
                FAISS Search: <strong className="text-text">{resultsData.faiss_ms} ms</strong>
              </span>
              <span className="flex items-center gap-1">
                <Database size={12} className="text-amber-500" />
                PostgreSQL Join: <strong className="text-text">{resultsData.db_ms} ms</strong>
              </span>
            </div>

            <div className="text-[11px] font-semibold text-accent">
              {resultsData.total} {resultsData.total === 1 ? "Chunk" : "Chunks"} Retrieved
            </div>
          </motion.div>
        )}

        {/* Error State */}
        {isError && (
          <div className="mt-6 p-4 bg-danger/10 border border-danger/20 rounded-xl flex items-start gap-3 text-xs text-danger">
            <AlertTriangle size={18} className="shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Retrieval Failed</p>
              <p className="mt-0.5 opacity-90">
                {errorObj?.response?.data?.detail || "Vector retrieval service encountered an unexpected error."}
              </p>
            </div>
          </div>
        )}

        {/* Results List */}
        {resultsData && (
          <div className="mt-6 space-y-4">
            {resultsData.results.length === 0 ? (
              <div className="py-12 text-center border border-dashed border-border rounded-xl p-6 bg-bg-alt/20">
                <div className="w-12 h-12 rounded-full bg-accent/10 text-accent flex items-center justify-center mx-auto mb-3">
                  <Info size={24} />
                </div>
                <h3 className="text-sm font-bold text-text">No Relevant Knowledge Found</h3>
                <p className="text-xs text-text-secondary mt-1 max-w-md mx-auto">
                  No indexed chunks matched your query above the similarity threshold ({threshold.toFixed(2)}).
                  Try broadening your search term or adjusting the scope.
                </p>
              </div>
            ) : (
              resultsData.results.map((item) => {
                const isExpanded = expandedChunkId === item.chunk_id;
                const isCopied = copiedChunkId === item.chunk_id;

                return (
                  <motion.div
                    key={item.chunk_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-5 bg-bg border border-border hover:border-accent/40 rounded-xl shadow-xs hover:shadow-md transition-all group relative"
                  >
                    {/* Header line */}
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <div className="flex items-center gap-2">
                        {/* Rank Badge */}
                        <span
                          className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono ${
                            item.rank === 1
                              ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                              : "bg-bg-alt text-text-secondary border border-border"
                          }`}
                        >
                          #{item.rank}
                        </span>

                        {/* Document Name */}
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-text">
                          <FileText size={14} className="text-accent" />
                          <span className="truncate max-w-[220px] sm:max-w-md">
                            {item.document_name}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {/* Similarity Score */}
                        <div className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-xs font-mono font-bold">
                          Score: {item.score.toFixed(4)}
                        </div>

                        {/* Copy button */}
                        <button
                          type="button"
                          onClick={() => handleCopy(item.content, item.chunk_id)}
                          className="p-1.5 text-text-secondary hover:text-text rounded-md hover:bg-bg-alt transition-colors"
                          title="Copy chunk text"
                        >
                          {isCopied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                        </button>
                      </div>
                    </div>

                    {/* Content text */}
                    <div className="text-xs text-text leading-relaxed font-sans bg-bg-alt/30 p-3.5 rounded-lg border border-border/50">
                      <p className={isExpanded ? "" : "line-clamp-3"}>{item.content}</p>
                    </div>

                    {/* Expand toggle */}
                    {item.content.length > 200 && (
                      <button
                        type="button"
                        onClick={() => setExpandedChunkId(isExpanded ? null : item.chunk_id)}
                        className="mt-2 text-[11px] font-semibold text-accent hover:underline flex items-center gap-1"
                      >
                        {isExpanded ? (
                          <>
                            <span>Show Less</span>
                            <ChevronUp size={12} />
                          </>
                        ) : (
                          <>
                            <span>Show Full Chunk</span>
                            <ChevronDown size={12} />
                          </>
                        )}
                      </button>
                    )}
                  </motion.div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
}
