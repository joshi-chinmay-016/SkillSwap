import api from "../services/api";

export interface RecommendationMentor {
  mentor_id: number;
  mentor_name: str;
  avatar_url?: string | null;
  department?: string | null;
  year?: number | null;
  compatibility_score: number;
  mentor_score: number;
  availability: boolean;
  average_rating: number;
  completed_sessions: number;
  feedback_count: number;
  verification_status: "CLAIMED" | "ASSESSED" | "VERIFIED" | "TRUSTED";
  credibility_score: number;
  matched_skills: string[];
  reasons: string[];
}

export const recommendationApi = {
  getMyRecommendations: async (limit: number = 10): Promise<RecommendationMentor[]> => {
    const res = await api.get("/recommendations/me", {
      params: { limit },
    });
    return res.data;
  },
};
