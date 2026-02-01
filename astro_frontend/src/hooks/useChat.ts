import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ChatSession, ChatRequest, ChatResponse } from "@/types";
import { useRelationshipStore } from "@/stores/relationshipStore";

// Query keys
export const chatKeys = {
  sessions: (aiCharacterId?: string) => 
    aiCharacterId ? ["chat-sessions", aiCharacterId] : ["chat-sessions"],
  session: (id: string) => ["chat-session", id] as const,
};

// Fetch chat sessions
export function useChatSessions(aiCharacterId?: string) {
  return useQuery({
    queryKey: chatKeys.sessions(aiCharacterId),
    queryFn: async () => {
      const params = aiCharacterId ? { ai_character_id: aiCharacterId } : {};
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

// Send message mutation with relationship tracking
export function useSendMessage() {
  const queryClient = useQueryClient();
  const updateRelationship = useRelationshipStore(
    (state) => state.updateFromResponse
  );

  return useMutation({
    mutationFn: async (data: ChatRequest) => {
      const response = await api.post<ChatResponse>("/chat", data);
      return response.data;
    },
    onSuccess: (data) => {
      // Update relationship store with new score (keyed by CHARACTER, not session)
      updateRelationship(
        data.ai_character_id,
        data.relationship_score,
        data.current_status,
        data.score_change
      );

      // Invalidate sessions to refetch updated history
      queryClient.invalidateQueries({ 
        queryKey: chatKeys.sessions(data.ai_character_id) 
      });
      queryClient.invalidateQueries({ 
        queryKey: chatKeys.session(data.session_id) 
      });
      // Also invalidate the character query to sync relationship data
      queryClient.invalidateQueries({
        queryKey: ["ai-character", data.ai_character_id]
      });
    },
  });
}
