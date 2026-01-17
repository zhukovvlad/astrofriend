import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Boyfriend, BoyfriendCreate } from "@/types";

// Query keys
export const boyfriendKeys = {
  all: ["boyfriends"] as const,
  detail: (id: string) => ["boyfriends", id] as const,
};

// Fetch all boyfriends
export function useBoyfriends() {
  return useQuery({
    queryKey: boyfriendKeys.all,
    queryFn: async () => {
      const response = await api.get<Boyfriend[]>("/boyfriends");
      return response.data;
    },
  });
}

// Fetch single boyfriend
export function useBoyfriend(id: string) {
  return useQuery({
    queryKey: boyfriendKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Boyfriend>(`/boyfriends/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

// Create boyfriend
export function useCreateBoyfriend() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: BoyfriendCreate) => {
      const response = await api.post<Boyfriend>("/boyfriends", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: boyfriendKeys.all });
    },
  });
}

// Delete boyfriend
export function useDeleteBoyfriend() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/boyfriends/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: boyfriendKeys.all });
    },
  });
}
