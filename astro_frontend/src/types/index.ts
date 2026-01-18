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
// BOYFRIEND TYPES
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

export interface Boyfriend {
  id: string;
  name: string;
  gender: string;
  birth_data: BirthData;
  system_prompt?: string | null;
  avatar_url?: string | null;
  created_at: string;
}

export interface BoyfriendCreate {
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
  boyfriend_id: string;
  title?: string;
  history: ChatMessage[];
  created_at: string;
}

export interface ChatSessionCreate {
  boyfriend_id: string;
  title?: string;
}

export interface ChatRequest {
  boyfriend_id: string;
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  boyfriend_id: string;
  user_message: string;
  ai_response: string;
}

// ============================================
// API ERROR TYPE
// ============================================
export interface ApiError {
  detail: string;
}
