// src/hooks/useMentorConversations.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listConversations,
  getConversation,
  getConversationMessages,
  createConversation,
  renameConversation,
  archiveConversation,
  deleteConversation,
  sendConversationMessage,
  retryMentorMessage,
} from "../api/mentorApi";
import type {
  MentorConversationCreate,
  MentorConversationListResponse,
  MentorConversation,
  MentorMessageListResponse,
  MentorConversationChatResponse,
} from "../types/mentor";

// Query keys
export const mentorKeys = {
  conversations: (status?: string) => ["mentor", "conversations", status || "ALL"] as const,
  conversation: (id: number | null) => ["mentor", "conversation", id] as const,
  messages: (id: number | null) => ["mentor", "messages", id] as const,
};

/**
 * Hook to fetch paginated list of conversations for current user.
 */
export function useMentorConversations(status?: string, page: number = 1, pageSize: number = 20) {
  return useQuery<MentorConversationListResponse, Error>({
    queryKey: mentorKeys.conversations(status),
    queryFn: () => listConversations(page, pageSize, status),
    staleTime: 30000,
  });
}

/**
 * Hook to fetch single conversation details.
 */
export function useMentorConversation(conversationId: number | null) {
  return useQuery<MentorConversation, Error>({
    queryKey: mentorKeys.conversation(conversationId),
    queryFn: () => getConversation(conversationId!),
    enabled: !!conversationId && !isNaN(conversationId),
    staleTime: 30000,
  });
}

/**
 * Hook to fetch paginated messages for a given conversation.
 */
export function useMentorMessages(conversationId: number | null, page: number = 1, pageSize: number = 50) {
  return useQuery<MentorMessageListResponse, Error>({
    queryKey: mentorKeys.messages(conversationId),
    queryFn: () => getConversationMessages(conversationId!, page, pageSize),
    enabled: !!conversationId && !isNaN(conversationId),
    staleTime: 10000,
  });
}

/**
 * Hook to create a new persistent conversation.
 */
export function useCreateMentorConversation() {
  const queryClient = useQueryClient();
  return useMutation<MentorConversation, Error, MentorConversationCreate | undefined>({
    mutationFn: (data) => createConversation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mentor", "conversations"] });
    },
  });
}

/**
 * Hook to rename conversation title.
 */
export function useRenameMentorConversation() {
  const queryClient = useQueryClient();
  return useMutation<MentorConversation, Error, { conversationId: number; title: string }>({
    mutationFn: ({ conversationId, title }) => renameConversation(conversationId, title),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: mentorKeys.conversation(updated.id) });
      queryClient.invalidateQueries({ queryKey: ["mentor", "conversations"] });
    },
  });
}

/**
 * Hook to archive a conversation.
 */
export function useArchiveMentorConversation() {
  const queryClient = useQueryClient();
  return useMutation<MentorConversation, Error, number>({
    mutationFn: (conversationId) => archiveConversation(conversationId),
    onSuccess: (archived) => {
      queryClient.invalidateQueries({ queryKey: mentorKeys.conversation(archived.id) });
      queryClient.invalidateQueries({ queryKey: ["mentor", "conversations"] });
    },
  });
}

/**
 * Hook to delete a conversation and remove from cache.
 */
export function useDeleteMentorConversation() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, number>({
    mutationFn: (conversationId) => deleteConversation(conversationId),
    onSuccess: (_, conversationId) => {
      queryClient.removeQueries({ queryKey: mentorKeys.conversation(conversationId) });
      queryClient.removeQueries({ queryKey: mentorKeys.messages(conversationId) });
      queryClient.invalidateQueries({ queryKey: ["mentor", "conversations"] });
    },
  });
}

/**
 * Hook to send a persistent chat message in a conversation.
 */
export function useSendMentorMessage(conversationId: number | null) {
  const queryClient = useQueryClient();
  return useMutation<MentorConversationChatResponse, Error, string>({
    mutationFn: (message: string) => sendConversationMessage(conversationId!, message),
    onSuccess: (data) => {
      // Invalidate messages, current conversation, and conversation list
      queryClient.invalidateQueries({ queryKey: mentorKeys.messages(data.conversation_id) });
      queryClient.invalidateQueries({ queryKey: mentorKeys.conversation(data.conversation_id) });
      queryClient.invalidateQueries({ queryKey: ["mentor", "conversations"] });
    },
  });
}

/**
 * Hook to retry generation for a USER message.
 */
export function useRetryMentorMessage(conversationId: number | null) {
  const queryClient = useQueryClient();
  return useMutation<MentorConversationChatResponse, Error, number>({
    mutationFn: (messageId: number) => retryMentorMessage(conversationId!, messageId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: mentorKeys.messages(data.conversation_id) });
      queryClient.invalidateQueries({ queryKey: mentorKeys.conversation(data.conversation_id) });
      queryClient.invalidateQueries({ queryKey: ["mentor", "conversations"] });
    },
  });
}
