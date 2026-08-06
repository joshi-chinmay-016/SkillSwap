import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../services/api";

/**
 * Fetch paginated list of documents with optional status filter and sort order.
 * Automatically polls every 2 seconds if any document is in UPLOADED or PROCESSING state.
 */
export function useDocuments({ status = null, page = 1, page_size = 20, sort = "newest" } = {}) {
  return useQuery({
    queryKey: ["documents", { status, page, page_size, sort }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (page) params.append("page", page.toString());
      if (page_size) params.append("page_size", page_size.toString());
      if (sort) params.append("sort", sort);

      const res = await api.get(`/documents?${params.toString()}`);
      return res.data;
    },
    staleTime: 5000,
    refetchInterval: (query) => {
      const docs = query.state.data?.documents || [];
      const hasActiveProcessing = docs.some(
        (doc) => doc.status === "PROCESSING" || doc.status === "UPLOADED"
      );
      return hasActiveProcessing ? 2000 : false;
    },
  });
}

/**
 * Fetch single document detail by ID.
 */
export function useDocument(documentId) {
  return useQuery({
    queryKey: ["documents", documentId],
    queryFn: async () => {
      if (!documentId) return null;
      const res = await api.get(`/documents/${documentId}`);
      return res.data;
    },
    enabled: Boolean(documentId),
    refetchInterval: (query) => {
      const doc = query.state.data;
      if (doc && (doc.status === "PROCESSING" || doc.status === "UPLOADED")) {
        return 2000;
      }
      return false;
    },
  });
}

/**
 * Alias hook for document metadata.
 */
export function useDocumentMetadata(documentId) {
  return useDocument(documentId);
}

/**
 * Fetch parsed text status and content for a document.
 */
export function useParsingStatus(documentId, enabled = true) {
  return useQuery({
    queryKey: ["parsedDocument", documentId],
    queryFn: async () => {
      if (!documentId) return null;
      try {
        const res = await api.get(`/documents/${documentId}/parsed`);
        return res.data;
      } catch (err) {
        if (err.response?.status === 404) {
          return { document_id: documentId, status: "PENDING", text_content: "", char_count: 0 };
        }
        throw err;
      }
    },
    enabled: Boolean(documentId) && enabled,
    refetchInterval: (query) => {
      const parsed = query.state.data;
      if (parsed && (parsed.status === "PENDING" || parsed.status === "PROCESSING")) {
        return 2000;
      }
      return false;
    },
  });
}

/**
 * Retry parsing a document.
 */
export function useRetryParsing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId) => {
      const res = await api.post(`/documents/${documentId}/retry`);
      return res.data;
    },
    onSuccess: (data, documentId) => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["documents", documentId] });
      queryClient.invalidateQueries({ queryKey: ["parsedDocument", documentId] });
    },
  });
}

/**
 * Upload a document with progress callback option.
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, onUploadProgress }) => {
      const formData = new FormData();
      formData.append("file", file);

      const res = await api.post("/documents/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          if (onUploadProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onUploadProgress(percent);
          }
        },
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["documentMetrics"] });
    },
  });
}

/**
 * Rename a document's display name.
 */
export function useRenameDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentId, displayName }) => {
      const res = await api.patch(`/documents/${documentId}`, {
        display_name: displayName,
      });
      return res.data;
    },
    onSuccess: (updatedDoc) => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["documents", updatedDoc.id] });
    },
  });
}

/**
 * Soft-delete (archive) a document.
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId) => {
      const res = await api.delete(`/documents/${documentId}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["documentMetrics"] });
    },
  });
}

/**
 * Download a document file as a blob and trigger browser download.
 */
export function useDownloadDocument() {
  return useMutation({
    mutationFn: async ({ documentId, filename }) => {
      const res = await api.get(`/documents/${documentId}/download`, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename || "document");
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
}

/**
 * Storage Health diagnostics.
 */
export function useStorageHealth() {
  return useQuery({
    queryKey: ["storageHealth"],
    queryFn: async () => {
      const res = await api.get("/documents/health");
      return res.data;
    },
    refetchInterval: 60000,
  });
}

/**
 * Storage / Document usage metrics.
 */
export function useDocumentMetrics() {
  return useQuery({
    queryKey: ["documentMetrics"],
    queryFn: async () => {
      const res = await api.get("/documents/metrics");
      return res.data;
    },
  });
}
