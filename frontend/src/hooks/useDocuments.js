import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../services/api";

/**
 * Fetch paginated list of documents with optional status filter and sort order.
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
    staleTime: 10000,
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

      // Create download link and click it
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
