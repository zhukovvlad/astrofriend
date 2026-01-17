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

// Response interceptor - handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Redirect to login on unauthorized
      // Cookie will be cleared by the server on logout
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
