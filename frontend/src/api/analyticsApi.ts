// src/api/analyticsApi.ts

import api from "../services/api";
import type { AnalyticsResponse } from "../types/analytics";

/**
 * Fetch analytics for the currently authenticated user.
 * Never passes user_id in query parameters to ensure security and prevent data leakage.
 */
export async function fetchAnalytics(params: Record<string, any> = {}): Promise<AnalyticsResponse> {
  // Exclude user_id if present to enforce authenticated user scope
  const { user_id, ...cleanParams } = params;
  const response = await api.get<AnalyticsResponse>("/activities/analytics", {
    params: cleanParams,
  });
  return response.data;
}
