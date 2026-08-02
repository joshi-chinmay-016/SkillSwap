// src/hooks/useMentorMemory.js

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMemories,
  getMemory,
  getMemoryStats,
  getMemorySettings,
  updateMemorySettings,
  updateMemory,
  archiveMemory,
  pinMemory,
  deleteMemory,
  createMemory,
} from "../api/mentorApi";

export const MENTOR_MEMORY_KEYS = {
  all: ["mentor-memory"],
  lists: () => [...MENTOR_MEMORY_KEYS.all, "list"],
  list: (filters) => [...MENTOR_MEMORY_KEYS.lists(), filters],
  details: () => [...MENTOR_MEMORY_KEYS.all, "detail"],
  detail: (id) => [...MENTOR_MEMORY_KEYS.details(), id],
  stats: () => [...MENTOR_MEMORY_KEYS.all, "stats"],
  settings: () => [...MENTOR_MEMORY_KEYS.all, "settings"],
};

export function useMentorMemory(filters = {}) {
  return useQuery({
    queryKey: MENTOR_MEMORY_KEYS.list(filters),
    queryFn: () => getMemories(filters),
    staleTime: 1000 * 30, // 30 seconds
  });
}

export function useMemory(id) {
  return useQuery({
    queryKey: MENTOR_MEMORY_KEYS.detail(id),
    queryFn: () => getMemory(id),
    enabled: Boolean(id),
  });
}

export function useMemoryStats() {
  return useQuery({
    queryKey: MENTOR_MEMORY_KEYS.stats(),
    queryFn: getMemoryStats,
    staleTime: 1000 * 30,
  });
}

export function useMemorySettings() {
  return useQuery({
    queryKey: MENTOR_MEMORY_KEYS.settings(),
    queryFn: getMemorySettings,
  });
}

export function useCreateMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data) => createMemory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.all });
    },
  });
}

export function useUpdateMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => updateMemory(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.stats() });
    },
  });
}

export function useArchiveMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => archiveMemory(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.stats() });
    },
  });
}

export function usePinMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isPinned }) => pinMemory(id, isPinned),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.stats() });
    },
  });
}

export function useDeleteMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => deleteMemory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.all });
    },
  });
}

export function useUpdateMemorySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data) => updateMemorySettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MENTOR_MEMORY_KEYS.settings() });
    },
  });
}
