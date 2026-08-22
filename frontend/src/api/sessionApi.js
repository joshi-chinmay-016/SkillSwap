import api from "../services/api";

/**
 * Authoritative API Client for Peer Learning Sessions & Learning Journeys
 */

// Peer Mentoring Sessions (/sessions)
export const bookPeerSession = async (payload, idempotencyKey) => {
  const headers = idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {};
  const res = await api.post("/sessions", payload, { headers });
  return res.data;
};

export const getMySessions = async () => {
  const res = await api.get("/sessions/me");
  return res.data;
};

export const getUpcomingSessions = async () => {
  const res = await api.get("/sessions/upcoming");
  return res.data;
};

export const getCompletedSessions = async () => {
  const res = await api.get("/sessions/completed");
  return res.data;
};

export const getCancelledSessions = async () => {
  const res = await api.get("/sessions/cancelled");
  return res.data;
};

export const getSessionCounts = async () => {
  const res = await api.get("/sessions/dashboard/counts");
  return res.data;
};

export const getSessionDetail = async (sessionId) => {
  const res = await api.get(`/sessions/${sessionId}`);
  return res.data;
};

export const getSessionParticipants = async (sessionId) => {
  const res = await api.get(`/sessions/${sessionId}/participants`);
  return res.data;
};

export const startPeerSession = async (sessionId) => {
  const res = await api.post(`/sessions/${sessionId}/start`);
  return res.data;
};

export const completePeerSession = async (sessionId) => {
  const res = await api.post(`/sessions/${sessionId}/complete`);
  return res.data;
};

export const cancelPeerSession = async (sessionId) => {
  const res = await api.post(`/sessions/${sessionId}/cancel`);
  return res.data;
};

export const joinPeerSession = async (sessionId) => {
  const res = await api.post(`/sessions/${sessionId}/join`);
  return res.data;
};

export const leavePeerSession = async (sessionId) => {
  const res = await api.post(`/sessions/${sessionId}/leave`);
  return res.data;
};

export const getSessionPresence = async (sessionId) => {
  const res = await api.get(`/sessions/${sessionId}/presence`);
  return res.data;
};

// Feedback APIs
export const submitSessionFeedback = async (payload) => {
  const res = await api.post("/feedback", payload);
  return res.data;
};

export const getSessionFeedbackList = async (sessionId) => {
  const res = await api.get(`/feedback/session/${sessionId}`);
  return res.data;
};

// Journey-Scoped Learning Sessions (/journeys/:id/sessions)
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
