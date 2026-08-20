import api from "../services/api";

export interface AssessmentQuestion {
  id: number;
  skill_id: number;
  question_text: string;
  options: string[];
  difficulty: string;
}

export interface AssessmentDetail {
  skill_id: number;
  skill_name: string;
  total_questions: number;
  passing_threshold_percent: number;
  questions: AssessmentQuestion[];
}

export interface AssessmentAnswerItem {
  question_id: number;
  selected_option: number;
}

export interface AssessmentResultDetail {
  question_id: number;
  selected_option: number;
  correct_option: number;
  is_correct: boolean;
  explanation?: string;
}

export interface AssessmentSubmissionResult {
  assessment_id: number;
  user_id: number;
  skill_id: number;
  user_skill_id: number;
  score: number;
  passed: boolean;
  total_questions: number;
  correct_answers: number;
  new_verification_status: string;
  details: AssessmentResultDetail[];
}

export interface SkillCredibilitySummary {
  user_id: number;
  skill_id: number;
  user_skill_id: number | null;
  verification_status: "CLAIMED" | "ASSESSED" | "VERIFIED" | "TRUSTED";
  credibility_score: number;
  claimed_at: string | null;
  verified_at: string | null;
  assessment: {
    attempted: boolean;
    latest_score: number | null;
    passed: boolean;
    total_attempts: number;
  };
  signals: {
    completed_teaching_sessions: number;
    feedback_count: number;
    average_rating: number;
    repeat_learners_count: number;
  };
  explanations: string[];
}

export interface UserOverallCredibility {
  user_id: number;
  overall_credibility_score: number;
  total_teach_skills: number;
  verified_skills_count: number;
  total_completed_sessions: number;
  overall_average_rating: number;
  total_feedback_count: number;
  skills: Array<{
    skill_id: number;
    skill_name: string;
    verification_status: string;
    credibility_score: number;
    assessment_score: number | null;
  }>;
}

export const verificationApi = {
  getSkillAssessment: async (skillId: number): Promise<AssessmentDetail> => {
    const res = await api.get(`/verification/skills/${skillId}/assessment`);
    return res.data;
  },

  submitSkillAssessment: async (
    skillId: number,
    answers: AssessmentAnswerItem[]
  ): Promise<AssessmentSubmissionResult> => {
    const res = await api.post(`/verification/skills/${skillId}/assessment`, {
      answers,
    });
    return res.data;
  },

  getSkillAssessmentResults: async (skillId: number) => {
    const res = await api.get(`/verification/skills/${skillId}/assessment/results`);
    return res.data;
  },

  getMyCredibility: async (): Promise<UserOverallCredibility> => {
    const res = await api.get("/verification/credibility/me");
    return res.data;
  },

  getUserCredibility: async (userId: number): Promise<UserOverallCredibility> => {
    const res = await api.get(`/verification/credibility/user/${userId}`);
    return res.data;
  },

  getSkillCredibility: async (skillId: number): Promise<SkillCredibilitySummary> => {
    const res = await api.get(`/verification/skills/${skillId}/credibility`);
    return res.data;
  },
};
