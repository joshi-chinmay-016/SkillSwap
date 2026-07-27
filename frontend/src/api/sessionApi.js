import api from "../services/api";

/**
 * API client for Learning Sessions (Day 59)
 */

export const createSession = async (journeyId, sessionData) => {
  const res = await api.post(`/journeys/${journeyId}/sessions`, sessionData);
  return res.data;
};

export const getJourneySessions = async (journeyId) => {
  const res = await api.get(`/journeys/${journeyId}/sessions`);
  return res.data;
};

export const getSession = async (sessionId) => {
  const res = await api.get(`/sessions/${sessionId}`);
  return res.data;
};

export const completeSession = async (sessionId) => {
  const res = await api.patch(`/sessions/${sessionId}/complete`);
  return res.data;
};

export const archiveSession = async (sessionId) => {
  const res = await api.patch(`/sessions/${sessionId}/archive`);
  return res.data;
};
