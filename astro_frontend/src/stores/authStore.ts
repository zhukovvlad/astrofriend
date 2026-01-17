import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";
import type { User, Token, UserCreate } from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: UserCreate) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          // OAuth2 form requires form-urlencoded
          const formData = new URLSearchParams();
          formData.append("username", email);
          formData.append("password", password);

          const response = await api.post<Token>("/auth/login", formData, {
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
          });

          const { access_token } = response.data;
          localStorage.setItem("access_token", access_token);
          
          set({ token: access_token, isAuthenticated: true, isLoading: false });
          
          // Fetch user data
          await get().fetchUser();
        } catch (error: any) {
          const message = error.response?.data?.detail || "Login failed";
          set({ error: message, isLoading: false });
          throw new Error(message);
        }
      },

      register: async (data: UserCreate) => {
        set({ isLoading: true, error: null });
        try {
          await api.post("/auth/register", data);
          // Auto-login after registration
          await get().login(data.email, data.password);
        } catch (error: any) {
          const message = error.response?.data?.detail || "Registration failed";
          set({ error: message, isLoading: false });
          throw new Error(message);
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        set({ token: null, user: null, isAuthenticated: false, error: null });
      },

      fetchUser: async () => {
        try {
          const response = await api.get<User>("/auth/me");
          set({ user: response.data });
        } catch (error) {
          // If fetch fails, clear auth state
          get().logout();
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ 
        token: state.token, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);
