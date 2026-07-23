import { useQuery } from "@tanstack/react-query";
import { fetchAnalytics } from "../api/analyticsApi";

/**
 * Custom React Query hook for fetching user learning analytics
 * Supports timeFilter parameter for filtering analytics view (7d, 30d, 90d, all)
 */
export function useAnalytics(timeFilter = "all") {
  return useQuery({
    queryKey: ["analytics", timeFilter],
    queryFn: () => fetchAnalytics({ timeframe: timeFilter }),
    staleTime: 5 * 60 * 1000, // 5 minutes cache
    refetchOnWindowFocus: false,
    retry: 1,
  });
}
