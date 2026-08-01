// src/types/mentor.ts

export interface MentorChatRequest {
  message: string;
}

export interface MentorChatResponse {
  response: string;
  recommended_topics: string[];
  difficulty_level: "Beginner" | "Intermediate" | "Advanced" | string;
  tool_used?: string | null;
  tool_success?: boolean | null;
  tool_execution_time?: number | null;
  tool_data?: Record<string, any> | null;
}

export interface MessageItem {
  id: string | number;
  role: "user" | "assistant" | "USER" | "ASSISTANT";
  content: string;
  timestamp?: string;
  created_at?: string;
  recommended_topics?: string[];
  difficulty_level?: string;
  isError?: boolean;
  tool_used?: string | null;
  tool_success?: boolean | null;
  tool_execution_time?: number | null;
  tool_data?: Record<string, any> | null;
}

// ──────────────────────────────────────────────────────────────────────────────
// Day 63 Persistent Conversation Types
// ──────────────────────────────────────────────────────────────────────────────

export interface MentorConversation {
  id: number;
  user_id: number;
  journey_id?: number | null;
  session_id?: number | null;
  title: string;

  status: "ACTIVE" | "ARCHIVED" | string;
  created_at: string;
  updated_at: string;
  last_message_at?: string | null;
}

export interface MentorMessage {
  id: number;
  conversation_id: number;
  role: "USER" | "ASSISTANT" | string;
  content: string;
  created_at: string;
  tool_used?: string | null;
  tool_success?: boolean | null;
  tool_execution_time?: number | null;
  tool_data?: Record<string, any> | null;
}

export interface MentorConversationCreate {
  title?: string;
  journey_id?: number;
  session_id?: number;
}

export interface MentorConversationUpdate {
  title: string;
}

export interface MentorConversationListResponse {
  conversations: MentorConversation[];
  total: number;
  page: number;
  page_size: number;
}

export interface MentorMessageListResponse {
  messages: MentorMessage[];
  total: number;
  page: number;
  page_size: number;
}

export interface MentorConversationChatResponse {
  conversation_id: number;
  user_message: MentorMessage;
  assistant_message: MentorMessage;
  recommended_topics: string[];
  difficulty_level: string;
  tool_used?: string | null;
  tool_success?: boolean | null;
  tool_execution_time?: number | null;
  tool_data?: Record<string, any> | null;
}
