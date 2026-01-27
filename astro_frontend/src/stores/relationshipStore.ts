import { create } from "zustand";
import { persist } from "zustand/middleware";

interface RelationshipData {
  score: number;
  status: string;
  lastScoreChange: number;
}

interface RelationshipState {
  // Map of character_id -> relationship data
  characters: Record<string, RelationshipData>;
}

interface RelationshipActions {
  // Update relationship from API response (keyed by character ID)
  updateFromResponse: (
    characterId: string,
    score: number,
    status: string,
    scoreChange: number
  ) => void;

  // Get relationship data for a character
  getCharacterRelationship: (characterId: string) => RelationshipData | null;

  // Clear score change indicator (after animation completes)
  clearScoreChange: (characterId: string) => void;

  // Reset a character's relationship
  resetCharacter: (characterId: string) => void;
  
  // Initialize from character data (e.g., when loading character)
  initFromCharacter: (characterId: string, score: number, status: string) => void;
}

const DEFAULT_RELATIONSHIP: RelationshipData = {
  score: 50,
  status: "Neutral",
  lastScoreChange: 0,
};

/**
 * Zustand store for managing relationship scores per AI Character.
 * Persisted to localStorage for consistency across page reloads.
 * 
 * Architecture: Relationship is tied to CHARACTER, not chat session.
 * This means the same character has the same attitude across all chat threads.
 */
export const useRelationshipStore = create<
  RelationshipState & RelationshipActions
>()(
  persist(
    (set, get) => ({
      characters: {},

      updateFromResponse: (characterId, score, status, scoreChange) => {
        set((state) => ({
          characters: {
            ...state.characters,
            [characterId]: {
              score,
              status,
              lastScoreChange: scoreChange,
            },
          },
        }));

        // Auto-clear score change after 3 seconds (for animation)
        setTimeout(() => {
          get().clearScoreChange(characterId);
        }, 3000);
      },
      
      initFromCharacter: (characterId, score, status) => {
        // Only init if we don't have data or if server data is different
        const current = get().characters[characterId];
        if (!current || current.score !== score || current.status !== status) {
          set((state) => ({
            characters: {
              ...state.characters,
              [characterId]: {
                score,
                status,
                lastScoreChange: 0,
              },
            },
          }));
        }
      },

      getCharacterRelationship: (characterId) => {
        return get().characters[characterId] || null;
      },

      clearScoreChange: (characterId) => {
        set((state) => {
          const character = state.characters[characterId];
          if (!character) return state;
          return {
            characters: {
              ...state.characters,
              [characterId]: {
                ...character,
                lastScoreChange: 0,
              },
            },
          };
        });
      },

      resetCharacter: (characterId) => {
        set((state) => {
          const newCharacters = { ...state.characters };
          delete newCharacters[characterId];
          return { characters: newCharacters };
        });
      },
    }),
    {
      name: "astro-relationships",
      partialize: (state) => ({
        // Only persist essential data, not lastScoreChange
        characters: Object.fromEntries(
          Object.entries(state.characters).map(([id, data]) => [
            id,
            { ...data, lastScoreChange: 0 },
          ])
        ),
      }),
    }
  )
);

/**
 * Hook for getting relationship state for a specific character
 * with reactive updates
 */
export function useCharacterRelationship(characterId: string | null | undefined) {
  const relationship = useRelationshipStore((state) =>
    characterId ? state.characters[characterId] : null
  );

  return relationship ?? DEFAULT_RELATIONSHIP;
}

/**
 * Hook for updating relationship from chat response
 */
export function useUpdateRelationship() {
  return useRelationshipStore((state) => state.updateFromResponse);
}

/**
 * Hook for initializing relationship from character data
 */
export function useInitRelationship() {
  return useRelationshipStore((state) => state.initFromCharacter);
}

export default useRelationshipStore;
