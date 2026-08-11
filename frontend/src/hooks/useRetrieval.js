import { useMutation, useQuery } from "@tanstack/react-query";
import api from "../services/api";

/**
 * React Query mutation for Semantic Knowledge Retrieval.
 * Executes POST /retrieval/search against backend FAISS & PostgreSQL engine.
 *
 * Payload: { query: string, top_k?: number, similarity_threshold?: number, document_id?: string }
 */
export function useRetrievalSearch() {
  return useMutation({
    mutationFn: async ({ query, top_k = 5, similarity_threshold = 0.0, document_id = null }) => {
      const payload = {
        query,
        top_k: Number(top_k),
        similarity_threshold: Number(similarity_threshold),
      };
      if (document_id) {
        payload.document_id = document_id;
      }
      const res = await api.post("/retrieval/search", payload);
      return res.data;
    },
  });
}
