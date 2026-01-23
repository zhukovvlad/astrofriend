import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AICharacter, AICharacterCreate } from "@/types";

// Query keys
export const aiCharacterKeys = {
  all: ["ai-characters"] as const,
  detail: (id: string) => ["ai-characters", id] as const,
};

// Fetch all AI characters
export function useAICharacters() {
  return useQuery({
    queryKey: aiCharacterKeys.all,
    queryFn: async () => {
      const response = await api.get<AICharacter[]>("/ai-characters");
      return response.data;
    },
  });
}

// Fetch single AI character
export function useAICharacter(id: string) {
  return useQuery({
    queryKey: aiCharacterKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<AICharacter>(`/ai-characters/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

// Create AI character
export function useCreateAICharacter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AICharacterCreate) => {
      const response = await api.post<AICharacter>("/ai-characters", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiCharacterKeys.all });
    },
  });
}

// Delete AI character
export function useDeleteAICharacter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/ai-characters/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiCharacterKeys.all });
    },
  });
}
