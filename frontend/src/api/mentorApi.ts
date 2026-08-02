// src/api/mentorApi.ts

import api from "../services/api";
import type {
  MentorChatRequest,
  MentorChatResponse,
  MentorConversation,
  MentorConversationCreate,
  MentorConversationUpdate,
  MentorConversationListResponse,
  MentorMessageListResponse,
  MentorConversationChatResponse,
} from "../types/mentor";

/**
  * Legacy stateless chat endpoint (Day 62 backward compatibility)
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

// ──────────────────────────────────────────────────────────────────────────────
// Day 63 Persistent Mentor Conversation API Functions
// ──────────────────────────────────────────────────────────────────────────────

export async function createConversation(
  data: MentorConversationCreate = {}
): Promise<MentorConversation> {
  const response = await api.post<MentorConversation>("/mentor/conversations", data);
  return response.data;
}

export async function listConversations(
  page: number = 1,
  pageSize: number = 20,
  status?: string
): Promise<MentorConversationListResponse> {
  const params: Record<string, any> = { page, page_size: pageSize };
  if (status) params.status = status;

  const response = await api.get<MentorConversationListResponse>("/mentor/conversations", {
    params,
  });
  return response.data;
}

export async function getConversation(conversationId: number): Promise<MentorConversation> {
  const response = await api.get<MentorConversation>(`/mentor/conversations/${conversationId}`);
  return response.data;
}

export async function renameConversation(
  conversationId: number,
  title: string
): Promise<MentorConversation> {
  const payload: MentorConversationUpdate = { title };
  const response = await api.patch<MentorConversation>(
    `/mentor/conversations/${conversationId}`,
    payload
  );
  return response.data;
}

export async function archiveConversation(conversationId: number): Promise<MentorConversation> {
  const response = await api.patch<MentorConversation>(
    `/mentor/conversations/${conversationId}/archive`
  );
  return response.data;
}

export async function deleteConversation(conversationId: number): Promise<void> {
  await api.delete(`/mentor/conversations/${conversationId}`);
}

export async function getConversationMessages(
  conversationId: number,
  page: number = 1,
  pageSize: number = 50
): Promise<MentorMessageListResponse> {
  const response = await api.get<MentorMessageListResponse>(
    `/mentor/conversations/${conversationId}/messages`,
    {
      params: { page, page_size: pageSize },
    }
  );
  return response.data;
}

export async function sendConversationMessage(
  conversationId: number,
  message: string
): Promise<MentorConversationChatResponse> {
  const response = await api.post<MentorConversationChatResponse>(
    `/mentor/conversations/${conversationId}/chat`,
    { message }
  );
  return response.data;
}

export async function retryMentorMessage(
  conversationId: number,
  messageId: number
): Promise<MentorConversationChatResponse> {
  const response = await api.post<MentorConversationChatResponse>(
    `/mentor/conversations/${conversationId}/messages/${messageId}/retry`
  );
  return response.data;
}

// ──────────────────────────────────────────────────────────────────────────────
// Day 65 Long-Term AI Memory API Functions
// ──────────────────────────────────────────────────────────────────────────────
import type {
  MentorMemory,
  MentorMemoryCreatePayload,
  MentorMemoryUpdatePayload,
  MentorMemoryListResponse,
  MentorMemoryStats,
  MentorMemorySettings,
  MentorMemorySettingsUpdatePayload,
  MemoryFilterParams,
} from "../types/mentorMemory";

export async function createMemory(data: MentorMemoryCreatePayload): Promise<MentorMemory> {
  const response = await api.post<MentorMemory>("/mentor/memory", data);
  return response.data;
}

export async function getMemories(
  filters: MemoryFilterParams = {}
): Promise<MentorMemoryListResponse> {
  const params: Record<string, any> = {};
  if (filters.category && filters.category !== "ALL") params.category = filters.category;
  if (filters.importance) params.importance = filters.importance;
  if (filters.status) params.status = filters.status;
  if (filters.search) params.search = filters.search;
  if (filters.page) params.page = filters.page;
  if (filters.pageSize) params.page_size = filters.pageSize;

  const response = await api.get<MentorMemoryListResponse>("/mentor/memory", { params });
  return response.data;
}

export async function getMemoryStats(): Promise<MentorMemoryStats> {
  const response = await api.get<MentorMemoryStats>("/mentor/memory/stats");
  return response.data;
}

export async function getMemorySettings(): Promise<MentorMemorySettings> {
  const response = await api.get<MentorMemorySettings>("/mentor/memory/settings");
  return response.data;
}

export async function updateMemorySettings(
  data: MentorMemorySettingsUpdatePayload
): Promise<MentorMemorySettings> {
  const response = await api.patch<MentorMemorySettings>("/mentor/memory/settings", data);
  return response.data;
}

export async function getMemory(id: number): Promise<MentorMemory> {
  const response = await api.get<MentorMemory>(`/mentor/memory/${id}`);
  return response.data;
}

export async function updateMemory(
  id: number,
  data: MentorMemoryUpdatePayload
): Promise<MentorMemory> {
  const response = await api.patch<MentorMemory>(`/mentor/memory/${id}`, data);
  return response.data;
}

export async function archiveMemory(id: number): Promise<MentorMemory> {
  const response = await api.patch<MentorMemory>(`/mentor/memory/${id}/archive`);
  return response.data;
}

export async function pinMemory(id: number, isPinned?: boolean): Promise<MentorMemory> {
  const response = await api.patch<MentorMemory>(`/mentor/memory/${id}/pin`, null, {
    params: isPinned !== undefined ? { is_pinned: isPinned } : {},
  });
  return response.data;
}

export async function deleteMemory(id: number): Promise<void> {
  await api.delete(`/mentor/memory/${id}`);
}

