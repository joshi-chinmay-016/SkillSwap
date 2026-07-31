// src/types/mentor.ts

export interface MentorChatRequest {
  message: string;
}

export interface MentorChatResponse {
  response: string;
  recommended_topics: string[];
  difficulty_level: "Beginner" | "Intermediate" | "Advanced" | string;
}

export interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  recommended_topics?: string[];
  difficulty_level?: string;
  isError?: boolean;
}
