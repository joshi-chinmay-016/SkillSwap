import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

api.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem("token");
      if (token) {
        // Strip extra quotes if stored as stringified JSON in Zustand
        const cleanToken = token.startsWith('"') && token.endsWith('"')
          ? JSON.parse(token)
          : token;
        config.headers.Authorization = `Bearer ${cleanToken}`;
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