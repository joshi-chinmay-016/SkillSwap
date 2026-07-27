// src/types/analytics.ts

export interface WeeklyActivity {
  [day: string]: number;
}

export interface MonthlyActivity {
  [month: string]: number;
}

export interface ActivityDistribution {
  [category: string]: number;
}

export interface LearningTrendInfo {
  percentage: number;
  direction: "up" | "down" | "stable";
}

export interface MostActiveDayInfo {
  day: string;
  count: number;
}

export interface AnalyticsSummaryInfo {
  total_activities: number;
  total_active_days: number;
  average_per_day: number;
  current_streak: number;
  longest_streak: number;
}

export interface AnalyticsResponse {
  weekly_activity: WeeklyActivity;
  monthly_activity: MonthlyActivity;
  activity_distribution: ActivityDistribution;
  learning_trend: LearningTrendInfo;
  learning_velocity: number;
  most_active_day?: MostActiveDayInfo | null;
  average_per_day: number;
  summary: AnalyticsSummaryInfo;
}
