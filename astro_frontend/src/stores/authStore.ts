import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";
import type { User, UserCreate } from "@/types";

/**
 * Authentication store using httpOnly cookie-based authentication.
 * 
 * Security benefits:
 * - Tokens stored in httpOnly cookies (not accessible via JavaScript)
 * - Protection against XSS attacks
 * - Session persists across page refreshes
 * - Server controls cookie lifecycle
 * 
 * Flow:
 * 1. Login: Server sets httpOnly cookie with JWT token
 * 2. Requests: Browser automatically includes cookie
 * 3. Logout: Server clears the cookie
 */

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: UserCreate) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
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

          // Server sets httpOnly cookie and returns user data
          const response = await api.post<User>("/auth/login", formData, {
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
          });

          set({ 
            user: response.data,
            isAuthenticated: true, 
            isLoading: false 
          });
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

      logout: async () => {
        try {
          // Call server to clear httpOnly cookie
          await api.post("/auth/logout");
        } catch (error) {
          // Continue with client-side cleanup even if server call fails
          console.error("Logout error:", error);
        }
        
        // Clear client state
        set({ user: null, isAuthenticated: false, error: null });
      },

      fetchUser: async () => {
        try {
          const response = await api.get<User>("/auth/me");
          set({ user: response.data, isAuthenticated: true });
        } catch (error) {
          // If fetch fails, clear auth state
          set({ user: null, isAuthenticated: false });
        }
      },

      checkAuth: async () => {
        /**
         * Check if user is authenticated by attempting to fetch user data.
         * This validates the httpOnly cookie on the server side.
         * Call this on app initialization to restore session.
         */
        set({ isLoading: true });
        try {
          const response = await api.get<User>("/auth/me");
          set({ user: response.data, isAuthenticated: true, isLoading: false });
        } catch (error) {
          // Cookie is invalid or expired
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      // Only persist user data for display purposes
      // Authentication state is validated via httpOnly cookie on checkAuth()
      partialize: (state) => ({ 
        user: state.user,
      }),
    }
  )
);
