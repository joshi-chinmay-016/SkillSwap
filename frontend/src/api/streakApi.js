// src/api/streakApi.js
import api from "../services/api";

/**
 * Fetch learning streak analytics for the authenticated user.
 * @returns {Promise<import('../types/streak').StreakResponse>} Streak data
 */
export const fetchStreak = async () => {
  const response = await api.get("/activities/streak");
  return response.data;
};

export default { fetchStreak };
