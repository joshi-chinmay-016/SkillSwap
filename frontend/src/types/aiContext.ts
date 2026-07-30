// src/types/aiContext.ts

export interface AIContextResponse {
  id: number;
  user_id: number;
  overall_summary: string | null;
  strong_topics: string[];
  weak_topics: string[];
  learning_interests: string[];
  recommended_topics: string[];
  learning_style: string | null;
  completed_sessions: number;
  context_version: number;
  created_at: string;
  updated_at: string;
}
