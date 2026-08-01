// src/hooks/useMentorChat.ts

import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { chatWithMentor } from "../api/mentorApi";
import type { MessageItem, MentorChatResponse } from "../types/mentor";

export function useMentorChat() {
  const [messages, setMessages] = useState<MessageItem[]>([]);

  const chatMutation = useMutation<MentorChatResponse, Error, string>({
    mutationFn: (message: string) => chatWithMentor(message),
    onSuccess: (data, variables) => {
      const assistantMsg: MessageItem = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.response,
        recommended_topics: data.recommended_topics || [],
        difficulty_level: data.difficulty_level || "Intermediate",
        tool_used: data.tool_used,
        tool_success: data.tool_success,
        tool_execution_time: data.tool_execution_time,
        tool_data: data.tool_data,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    },
    onError: (error, variables) => {
      const errorMsg: MessageItem = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Unable to contact your AI Mentor. Please check your connection and try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    },
  });

  const sendMessage = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed || chatMutation.isPending) return;

    const userMsg: MessageItem = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    chatMutation.mutate(trimmed);
  }, [chatMutation]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    sendMessage,
    clearMessages,
    isThinking: chatMutation.isPending,
    isError: chatMutation.isError,
    error: chatMutation.error,
  };
}
