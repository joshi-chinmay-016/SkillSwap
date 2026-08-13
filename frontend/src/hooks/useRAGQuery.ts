// src/hooks/useRAGQuery.ts

import { useMutation } from "@tanstack/react-query";
import { queryRAG, RAGQueryRequest, RAGQueryResponse } from "../api/ragApi";

/**
 * React Query mutation hook for executing single-query Grounded RAG.
 * Uses the authentic backend POST /rag/query endpoint.
 */
export function useRAGQuery() {
  return useMutation<RAGQueryResponse, Error, RAGQueryRequest>({
    mutationFn: async (payload: RAGQueryRequest) => {
      return await queryRAG(payload);
    },
  });
}
