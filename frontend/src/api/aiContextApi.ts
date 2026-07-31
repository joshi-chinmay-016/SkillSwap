// src/api/aiContextApi.ts

import api from "../services/api";
import type { AIContextResponse } from "../types/aiContext";

/**
 * Fetch persistent AI Context for the authenticated user.
 */
export async function getAIContext(): Promise<AIContextResponse> {
  const response = await api.get<AIContextResponse>("/users/me/context");
  return response.data;
}

/**
 * Trigger explicit AI Context regeneration.
 */
export async function regenerateAIContext(): Promise<AIContextResponse> {
  const response = await api.post<AIContextResponse>("/users/me/context/regenerate");
  return response.data;
}
