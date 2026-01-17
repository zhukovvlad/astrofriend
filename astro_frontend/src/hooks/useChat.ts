import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ChatSession, ChatRequest, ChatResponse } from "@/types";

// Query keys
export const chatKeys = {
  sessions: (boyfriendId?: string) => 
    boyfriendId ? ["chat-sessions", boyfriendId] : ["chat-sessions"],
  session: (id: string) => ["chat-session", id] as const,
};

// Fetch chat sessions
export function useChatSessions(boyfriendId?: string) {
  return useQuery({
    queryKey: chatKeys.sessions(boyfriendId),
    queryFn: async () => {
      const params = boyfriendId ? { boyfriend_id: boyfriendId } : {};
      const response = await api.get<ChatSession[]>("/chat/sessions", { params });
      return response.data;
    },
  });
}

// Fetch single chat session
export function useChatSession(sessionId: string) {
  return useQuery({
    queryKey: chatKeys.session(sessionId),
    queryFn: async () => {
      const response = await api.get<ChatSession>(`/chat/sessions/${sessionId}`);
      return response.data;
    },
    enabled: !!sessionId,
  });
}

// Send message mutation
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ChatRequest) => {
      const response = await api.post<ChatResponse>("/chat", data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate sessions to refetch updated history
      queryClient.invalidateQueries({ 
        queryKey: chatKeys.sessions(data.boyfriend_id) 
      });
      queryClient.invalidateQueries({ 
        queryKey: chatKeys.session(data.session_id) 
      });
    },
  });
}
