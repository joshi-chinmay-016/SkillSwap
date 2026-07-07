import axios from "axios";
import { useAuthStore } from "../store/authStore";

const api = axios.create({
  baseURL: "http://localhost:8000",
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

export default api;