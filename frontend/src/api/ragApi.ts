// src/api/ragApi.ts

import api from "../services/api";

export interface RAGSource {
  chunk_id: string;
  document_id: string;
  document_name: string;
  rank: number;
  score: number;
}

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
  document_id?: string | null;
  response_style?: "concise" | "detailed" | "explanatory";
}

export interface RAGQueryResponse {
  answer: string;
  sources: RAGSource[];
  insufficient_context: boolean;
  context_chunk_count: number;
  model: string;
}

/**
 * Execute single-query Grounded RAG generation via backend API (/rag/query).
 */
export async function queryRAG(payload: RAGQueryRequest): Promise<RAGQueryResponse> {
  const response = await api.post<RAGQueryResponse>("/rag/query", payload);
  return response.data;
}
