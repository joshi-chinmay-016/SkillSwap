// src/hooks/useAIContext.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAIContext, regenerateAIContext } from "../api/aiContextApi";
import type { AIContextResponse } from "../types/aiContext";

export function useAIContext() {
  const queryClient = useQueryClient();

  const contextQuery = useQuery<AIContextResponse, Error>({
    queryKey: ["aiContext", "me"],
    queryFn: getAIContext,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  const regenerateMutation = useMutation<AIContextResponse, Error>({
    mutationFn: regenerateAIContext,
    onSuccess: (newData) => {
      queryClient.setQueryData(["aiContext", "me"], newData);
    },
  });

  return {
    context: contextQuery.data ?? null,
    isLoading: contextQuery.isLoading,
    isError: contextQuery.isError,
    error: contextQuery.error,
    refetch: contextQuery.refetch,
    regenerate: regenerateMutation.mutate,
    isRegenerating: regenerateMutation.isPending,
  };
}
