// ============================================
// USER TYPES
// ============================================
export interface User {
  id: string;
  email: string;
  telegram_id?: number | null;
  is_active: boolean;
  created_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// ============================================
// AI CHARACTER TYPES
// ============================================
export interface BirthData {
  name: string;
  year: number;
  month: number;
  day: number;
  hour?: number;
  minute?: number;
  city?: string;
  nation?: string;
}

export interface AICharacter {
  id: string;
  name: string;
  gender: string;
  birth_data: BirthData;
  system_prompt?: string | null;
  avatar_url?: string | null;
  relationship_score: number;
  current_status: string;
  created_at: string;
}

export interface AICharacterCreate {
  name: string;
  gender?: string;
  birth_data: BirthData;
}

// ============================================
// CHAT TYPES
// ============================================
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface ChatSession {
  id: string;
  ai_character_id: string;
  title?: string;
  history: ChatMessage[];
  created_at: string;
}

export interface ChatSessionCreate {
  ai_character_id: string;
  title?: string;
}

export interface ChatRequest {
  ai_character_id: string;
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  ai_character_id: string;
  user_message: string;
  ai_response: string;
  relationship_score: number;
  current_status: string;
  score_change: number;
  internal_thought?: string;
}

// ============================================
// API ERROR TYPE
// ============================================
export interface ApiError {
  detail: string;
}
