import { useQuery } from "@tanstack/react-query";
import { fetchHeatmap } from "../api/activityApi";

/**
 * Custom hook to fetch and cache learning activity heatmap data using React Query.
 *
 * Configured with queryKey ["activities", "heatmap"] so invalidating "activities"
 * or "heatmap" automatically refreshes the contribution calendar graph.
 *
 * @returns {import('@tanstack/react-query').UseQueryResult<import('../api/activityApi').HeatmapResponse>}
 */
export function useHeatmap() {
  return useQuery({
    queryKey: ["activities", "heatmap"],
    queryFn: fetchHeatmap,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,    // 10 minutes
  });
}

export default useHeatmap;
