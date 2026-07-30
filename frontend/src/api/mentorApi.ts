// src/api/mentorApi.ts

import api from "../services/api";
import type { MentorChatRequest, MentorChatResponse } from "../types/mentor";

/**
 * Send a user message to the Context-Aware AI Learning Mentor.
 */
export async function chatWithMentor(message: string): Promise<MentorChatResponse> {
  const payload: MentorChatRequest = { message };
  const response = await api.post<MentorChatResponse>("/mentor/chat", payload);
  return response.data;
}

/**
 * Health check for the AI Mentor service.
 */
export async function getMentorHealth(): Promise<{ status: string }> {
  const response = await api.get<{ status: string }>("/mentor/health");
  return response.data;
}
