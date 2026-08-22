import api from "../services/api";

/**
 * Availability API client for SkillSwap Arena
 */

export const getMyAvailability = async () => {
  const res = await api.get("/availability/me");
  return res.data;
};

export const createAvailability = async (payload) => {
  const res = await api.post("/availability", payload);
  return res.data;
};

export const createAllTimeAvailability = async (payload = {}) => {
  const res = await api.post("/availability/all-time", payload);
  return res.data;
};

export const deleteAvailability = async (slotId) => {
  const res = await api.delete(`/availability/${slotId}`);
  return res.data;
};

export const getMentorAvailabilityWindows = async (mentorId) => {
  const res = await api.get(`/availability/mentor/${mentorId}`);
  return res.data;
};

export const getMentorBookableSlots = async (mentorId, dateStr) => {
  const res = await api.get(`/availability/mentor/${mentorId}/slots`, {
    params: { date: dateStr },
  });
  return res.data;
};
