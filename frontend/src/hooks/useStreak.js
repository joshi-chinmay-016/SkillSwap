// src/hooks/useStreak.js
import { useQuery } from "@tanstack/react-query";
import { fetchStreak } from "../api/streakApi";

/**
 * Hook to fetch learning streak analytics.
 * Returns data, loading, error, and refetch.
 */
export const useStreak = () => {
  const query = useQuery({
    queryKey: ["streak"],
    queryFn: fetchStreak,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    retry: false,
  });
  return query;
};
