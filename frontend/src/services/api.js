import axios from "axios";
import { useAuthStore } from "../store/authStore";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

api.interceptors.request.use(
  (config) => {
    try {
      // Get token from authStore instead of localStorage directly
      const token = useAuthStore.getState().token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      console.error("Error setting Authorization header:", e);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const requestUrl = error.config?.url || "";
      const isAuthEndpoint = requestUrl.includes("/auth/login") || requestUrl.includes("/auth/register");
      
      if (!isAuthEndpoint && window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        console.warn("Unauthorized API call. Logging out...");
        // Logout and clear token
        useAuthStore.getState().logout();
        // Redirect to login page
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;