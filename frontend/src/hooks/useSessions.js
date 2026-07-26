import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createSession,
  getJourneySessions,
  getSession,
  completeSession,
  archiveSession,
} from "../api/sessionApi";

/**
 * Hook to fetch sessions for a specific journey
 */
export const useJourneySessions = (journeyId) => {
  return useQuery({
    queryKey: ["journey-sessions", journeyId],
    queryFn: () => getJourneySessions(journeyId),
    enabled: !!journeyId,
  });
};

/**
 * Hook to fetch a single learning session by ID
 */
export const useLearningSession = (sessionId) => {
  return useQuery({
    queryKey: ["learning-session", sessionId],
    queryFn: () => getSession(sessionId),
    enabled: !!sessionId,
  });
};

/**
 * Hook to create a new learning session
 */
export const useCreateSession = (journeyId) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionData) => createSession(journeyId, sessionData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["journey-sessions", journeyId] });
      queryClient.invalidateQueries({ queryKey: ["journey", journeyId] });
    },
  });
};

/**
 * Hook to complete a learning session
 * Invalidates sessions, journey, activities, heatmap, streak, analytics, and achievements
 */
export const useCompleteSession = (journeyId) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId) => completeSession(sessionId),
    onSuccess: (data, sessionId) => {
      // Invalidate session lists & detail
      queryClient.invalidateQueries({ queryKey: ["journey-sessions", journeyId] });
      queryClient.invalidateQueries({ queryKey: ["learning-session", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["journey", journeyId] });

      // Invalidate ecosystem metrics
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["heatmap"] });
      queryClient.invalidateQueries({ queryKey: ["streak"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      queryClient.invalidateQueries({ queryKey: ["achievements-progress"] });
    },
  });
};

/**
 * Hook to archive a learning session
 */
export const useArchiveSession = (journeyId) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId) => archiveSession(sessionId),
    onSuccess: (data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ["journey-sessions", journeyId] });
      queryClient.invalidateQueries({ queryKey: ["learning-session", sessionId] });
    },
  });
};
