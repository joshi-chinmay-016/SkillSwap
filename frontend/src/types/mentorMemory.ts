// src/types/mentorMemory.ts

export type MemoryCategory =
  | "LEARNING_STYLE"
  | "LONG_TERM_GOAL"
  | "STRONG_TOPIC"
  | "WEAK_TOPIC"
  | "LEARNING_PREFERENCE"
  | "FREQUENT_TOPIC"
  | "ACHIEVEMENT"
  | "PERSONAL_PREFERENCE"
  | "GENERAL";

export type MemoryImportance = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type MemoryStatus = "ACTIVE" | "ARCHIVED";

export type MemorySource =
  | "Conversation"
  | "AI Context"
  | "Learning Session"
  | "Session Summary"
  | "Journey"
  | "Tool"
  | "Manual";

export interface MentorMemory {
  id: number;
  user_id: number;
  category: MemoryCategory | string;
  title: string;
  content: string;
  importance: MemoryImportance | string;
  source: MemorySource | string;
  status: MemoryStatus | string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string | null;
  why_remembered?: string | null;
}

export interface MentorMemoryCreatePayload {
  category: MemoryCategory | string;
  title: string;
  content: string;
  importance?: MemoryImportance | string;
  source?: MemorySource | string;
  is_pinned?: boolean;
}

export interface MentorMemoryUpdatePayload {
  category?: MemoryCategory | string;
  title?: string;
  content?: string;
  importance?: MemoryImportance | string;
  source?: MemorySource | string;
  is_pinned?: boolean;
}

export interface MentorMemoryListResponse {
  memories: MentorMemory[];
  total: number;
  page: number;
  page_size: number;
}

export interface MentorMemoryStats {
  total_memories: number;
  pinned_count: number;
  high_importance_count: number;
  recently_used_count: number;
  category_distribution: Record<string, number>;
  importance_distribution: Record<string, number>;
  most_used_category?: string | null;
  oldest_memory_date?: string | null;
  newest_memory_date?: string | null;
}

export interface MentorMemorySettings {
  memory_enabled: boolean;
  automatic_extraction: boolean;
  automatic_updates: boolean;
  memory_notifications: boolean;
}

export interface MentorMemorySettingsUpdatePayload {
  memory_enabled?: boolean;
  automatic_extraction?: boolean;
  automatic_updates?: boolean;
  memory_notifications?: boolean;
}

export interface MemoryFilterParams {
  category?: string;
  importance?: string;
  status?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}
