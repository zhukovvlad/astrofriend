import axios, { type AxiosError } from "axios";
import type { ApiError } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Axios instance configured for httpOnly cookie authentication.
 * 
 * The server sets httpOnly secure cookies on login, and the browser
 * automatically includes them in requests when withCredentials is true.
 * 
 * Benefits:
 * - Tokens are not accessible via JavaScript (XSS protection)
 * - Automatic cookie handling by the browser
 * - Session persists across page refreshes
 */
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  // Required for cookies to be sent with cross-origin requests
  withCredentials: true,
});

// Response interceptor - handle 401 errors intelligently
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Check if we should skip automatic redirect to login
      const currentPath = window.location.pathname;
      const requestUrl = error.config?.url || "";
      const skipRedirect = error.config?.headers?.["x-skip-401-redirect"];
      
      const shouldSkipRedirect = 
        // Already on auth page
        currentPath === "/login" || 
        currentPath === "/register" ||
        // Request was to auth endpoint (let the component handle it)
        requestUrl.includes("/auth/login") ||
        requestUrl.includes("/auth/register") ||
        // Explicit opt-out via header
        skipRedirect === "true";
      
      if (!shouldSkipRedirect) {
        // Redirect to login for unauthorized requests
        // Cookie will be cleared by the server on logout
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
