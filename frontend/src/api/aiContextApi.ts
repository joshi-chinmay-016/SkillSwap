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

/**
 * Update user-editable AI Context fields (learning_interests, learning_style).
 */
export async function updateAIContext(data: {
  learning_interests?: string[];
  learning_style?: string;
}): Promise<AIContextResponse> {
  const response = await api.patch<AIContextResponse>("/users/me/context", data);
  return response.data;
}
