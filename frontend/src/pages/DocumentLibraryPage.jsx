import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useToast } from "../components/common/Toast";
import {
  useDocuments,
  useUploadDocument,
  useRenameDocument,
  useDeleteDocument,
  useDownloadDocument,
  useStorageHealth,
  useDocumentMetrics,
} from "../hooks/useDocuments";

import Hero from "../components/documents/Hero";
import UploadZone from "../components/documents/UploadZone";
import UploadQueue from "../components/documents/UploadQueue";
import FloatingToolbar from "../components/documents/FloatingToolbar";
import DocumentGrid from "../components/documents/DocumentGrid";
import EmptyLibrary from "../components/documents/EmptyLibrary";
import { SkeletonGrid } from "../components/documents/SkeletonCard";
import DocumentPreview from "../components/documents/DocumentPreview";
import RenameModal from "../components/documents/RenameModal";
import DeleteDialog from "../components/documents/DeleteDialog";

import { ChevronLeft, ChevronRight, AlertCircle, RefreshCw } from "lucide-react";

export default function DocumentLibraryPage() {
  const toast = useToast();

  // Toolbar & State
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [selectedSort, setSelectedSort] = useState("newest");
  const [viewMode, setViewMode] = useState("grid");
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Queue state for multi-file uploads
  const [uploadQueue, setUploadQueue] = useState([]);

  // Modal States
  const [previewDoc, setPreviewDoc] = useState(null);
  const [renameDoc, setRenameDoc] = useState(null);
  const [deleteDoc, setDeleteDoc] = useState(null);

  // Queries
  const {
    data: documentsData,
    isLoading,
    isError,
    refetch,
  } = useDocuments({ page, page_size: pageSize, sort: selectedSort });

  const { data: healthData } = useStorageHealth();
  const { data: metricsData } = useDocumentMetrics();

  // Mutations
  const uploadMutation = useUploadDocument();
  const renameMutation = useRenameDocument();
  const deleteMutation = useDeleteDocument();
  const downloadMutation = useDownloadDocument();

  // Process files selected for upload (single or multiple)
  const handleFilesSelected = async (files) => {
    if (!files || files.length === 0) return;

    const newQueueItems = files.map((file) => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      filename: file.name,
      progress: 0,
      status: "uploading",
      error: null,
    }));

    setUploadQueue((prev) => [...newQueueItems, ...prev]);

    // Process each file in the queue
    for (const item of newQueueItems) {
      try {
        await uploadMutation.mutateAsync({
          file: item.file,
          onUploadProgress: (percent) => {
            setUploadQueue((prev) =>
              prev.map((q) => (q.id === item.id ? { ...q, progress: percent } : q))
            );
          },
        });

        // Mark as success
        setUploadQueue((prev) =>
          prev.map((q) =>
            q.id === item.id ? { ...q, progress: 100, status: "success" } : q
          )
        );

        toast.success(
          `'${item.filename}' uploaded successfully to your AI Library.`,
          "Upload Complete"
        );

        // Auto remove success items after 3 seconds
        setTimeout(() => {
          setUploadQueue((prev) => prev.filter((q) => q.id !== item.id));
        }, 3000);
      } catch (err) {
        const errorMsg =
          err.response?.data?.detail || "Upload failed. Please check file type and size.";

        setUploadQueue((prev) =>
          prev.map((q) =>
            q.id === item.id ? { ...q, status: "error", error: errorMsg } : q
          )
        );

        toast.error(errorMsg, "Upload Error");
      }
    }
  };

  const handleDismissQueueItem = (id) => {
    setUploadQueue((prev) => prev.filter((q) => q.id !== id));
  };

  const handleRetryQueueItem = (id) => {
    const item = uploadQueue.find((q) => q.id === id);
    if (item) {
      setUploadQueue((prev) => prev.filter((q) => q.id !== id));
      handleFilesSelected([item.file]);
    }
  };

  // Filter & Search logic
  const filteredDocuments = useMemo(() => {
    if (!documentsData?.documents) return [];

    return documentsData.documents.filter((doc) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = (doc.display_name || "").toLowerCase().includes(q);
        const matchesFile = (doc.original_filename || "").toLowerCase().includes(q);
        if (!matchesName && !matchesFile) return false;
      }

      // 2. Filter Pills (All / PDF / TXT / Markdown)
      if (selectedFilter !== "all") {
        const ext = (doc.file_extension || "").toLowerCase();
        if (selectedFilter === "pdf" && ext !== "pdf") return false;
        if (selectedFilter === "txt" && ext !== "txt") return false;
        if (selectedFilter === "md" && ext !== "md") return false;
      }

      return true;
    });
  }, [documentsData?.documents, searchQuery, selectedFilter]);

  // Rename Action Handler
  const handleConfirmRename = async (documentId, newDisplayName) => {
    try {
      await renameMutation.mutateAsync({ documentId, displayName: newDisplayName });
      toast.success(`Renamed to '${newDisplayName}'.`, "Document Renamed");
    } catch (err) {
      toast.error(
        err.response?.data?.detail || "Failed to rename document.",
        "Rename Error"
      );
    }
  };

  // Delete Action Handler
  const handleConfirmDelete = async (documentId) => {
    try {
      await deleteMutation.mutateAsync(documentId);
      toast.success("Document has been archived.", "Deleted");
    } catch (err) {
      toast.error(
        err.response?.data?.detail || "Failed to delete document.",
        "Delete Error"
      );
    }
  };

  // Download Action Handler
  const handleDownload = async (doc) => {
    try {
      toast.info(`Downloading '${doc.original_filename}'...`, "Download Started");
      await downloadMutation.mutateAsync({
        documentId: doc.id,
        filename: doc.original_filename,
      });
    } catch (err) {
      toast.error(
        err.response?.data?.detail || "Failed to download document.",
        "Download Error"
      );
    }
  };

  // Smooth Page Scroll to Top on Pagination
  const handlePageChange = (newPage) => {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const isHealthy = healthData?.healthy ?? true;
  const totalDocsCount = documentsData?.total || 0;
  const totalBytesCount = metricsData?.total_bytes_uploaded || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="space-y-6"
    >
      {/* Hero Section */}
      <Hero
        totalDocuments={totalDocsCount}
        totalBytes={totalBytesCount}
        isHealthy={isHealthy}
        onQuickUpload={() => {
          const el = document.getElementById("document-file-input");
          if (el) el.click();
        }}
      />

      {/* Drag & Drop Upload Zone */}
      <UploadZone onFilesSelected={handleFilesSelected} />

      {/* Animated Upload Queue */}
      <UploadQueue
        queue={uploadQueue}
        onDismissItem={handleDismissQueueItem}
        onRetryItem={handleRetryQueueItem}
      />

      {/* Glass Floating Toolbar */}
      <FloatingToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedFilter={selectedFilter}
        onFilterChange={setSelectedFilter}
        selectedSort={selectedSort}
        onSortChange={setSelectedSort}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* Main Content Area */}
      {isLoading ? (
        <SkeletonGrid count={8} viewMode={viewMode} />
      ) : isError ? (
        <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-danger/30 bg-danger/5 my-6">
          <AlertCircle size={40} className="text-danger mb-3" />
          <h3 className="text-base font-bold text-text mb-1">Failed to load documents</h3>
          <p className="text-xs text-text-secondary mb-4">
            Could not retrieve your document library. Please check your connection.
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-danger text-white text-xs font-semibold hover:bg-danger/90 transition-colors cursor-pointer"
          >
            <RefreshCw size={14} />
            <span>Try Again</span>
          </button>
        </div>
      ) : filteredDocuments.length === 0 ? (
        <EmptyLibrary
          onUploadClick={() => {
            const el = document.getElementById("document-file-input");
            if (el) el.click();
          }}
        />
      ) : (
        <DocumentGrid
          documents={filteredDocuments}
          viewMode={viewMode}
          onPreview={(doc) => setPreviewDoc(doc)}
          onRename={(doc) => setRenameDoc(doc)}
          onDownload={handleDownload}
          onDelete={(doc) => setDeleteDoc(doc)}
        />
      )}

      {/* Pagination Footer */}
      {documentsData && (documentsData.has_next || documentsData.has_previous) && (
        <div className="flex items-center justify-between pt-6 border-t border-border/80 text-xs">
          <span className="text-text-secondary font-medium">
            Page <span className="font-bold text-text">{page}</span> of{" "}
            <span className="font-bold text-text">
              {Math.ceil(documentsData.total / pageSize)}
            </span>
          </span>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={!documentsData.has_previous}
              onClick={() => handlePageChange(page - 1)}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-border bg-bg hover:bg-bg-alt text-text font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              <ChevronLeft size={14} />
              <span>Previous</span>
            </button>

            <button
              type="button"
              disabled={!documentsData.has_next}
              onClick={() => handlePageChange(page + 1)}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-border bg-bg hover:bg-bg-alt text-text font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              <span>Next</span>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Modals & Dialogs */}
      <DocumentPreview
        document={previewDoc}
        isOpen={Boolean(previewDoc)}
        onClose={() => setPreviewDoc(null)}
        onRename={(doc) => setRenameDoc(doc)}
        onDownload={handleDownload}
        onDelete={(doc) => setDeleteDoc(doc)}
      />

      <RenameModal
        document={renameDoc}
        isOpen={Boolean(renameDoc)}
        onClose={() => setRenameDoc(null)}
        onConfirm={handleConfirmRename}
      />

      <DeleteDialog
        document={deleteDoc}
        isOpen={Boolean(deleteDoc)}
        onClose={() => setDeleteDoc(null)}
        onConfirm={handleConfirmDelete}
      />
    </motion.div>
  );
}
