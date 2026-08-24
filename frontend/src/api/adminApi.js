import api from "../services/api";

/**
 * Authoritative API Client for Platform Administration (Phase 8.3 & 8.4)
 */

export const getAdminDashboard = async () => {
  const res = await api.get("/admin/dashboard");
  return res.data;
};

export const getAdminUsers = async (params = {}) => {
  const res = await api.get("/admin/users", { params });
  return res.data;
};

export const suspendAdminUser = async (userId, reason) => {
  const res = await api.post(`/admin/users/${userId}/suspend`, { reason });
  return res.data;
};

export const reactivateAdminUser = async (userId, reason) => {
  const res = await api.post(`/admin/users/${userId}/reactivate`, { reason });
  return res.data;
};

export const updateAdminUserRole = async (userId, role, reason) => {
  const res = await api.post(`/admin/users/${userId}/role`, { role, reason });
  return res.data;
};

export const getAdminSkills = async (params = {}) => {
  const res = await api.get("/admin/skills", { params });
  return res.data;
};

export const createAdminSkill = async (data) => {
  const res = await api.post("/admin/skills", data);
  return res.data;
};

export const updateAdminSkill = async (skillId, data) => {
  const res = await api.put(`/admin/skills/${skillId}`, data);
  return res.data;
};

export const getAdminVerifications = async (params = {}) => {
  const res = await api.get("/admin/verification", { params });
  return res.data;
};

export const approveAdminVerification = async (userSkillId, reason, scoreOverride = null) => {
  const res = await api.post(`/admin/verification/${userSkillId}/approve`, {
    reason,
    score_override: scoreOverride,
  });
  return res.data;
};

export const rejectAdminVerification = async (userSkillId, reason) => {
  const res = await api.post(`/admin/verification/${userSkillId}/reject`, { reason });
  return res.data;
};

export const getAdminSessions = async (params = {}) => {
  const res = await api.get("/admin/sessions", { params });
  return res.data;
};

export const cancelAdminSession = async (sessionId, reason, refundCoins = true) => {
  const res = await api.post(`/admin/sessions/${sessionId}/cancel`, {
    reason,
    refund_coins: refundCoins,
  });
  return res.data;
};

export const getAdminReports = async (params = {}) => {
  const res = await api.get("/admin/reports", { params });
  return res.data;
};

export const resolveAdminReport = async (reportId, status, resolutionNotes) => {
  const res = await api.post(`/admin/reports/${reportId}/resolve`, {
    status,
    resolution_notes: resolutionNotes,
  });
  return res.data;
};

export const getAdminWallet = async (params = {}) => {
  const res = await api.get("/admin/wallet", { params });
  return res.data;
};

export const adjustAdminWallet = async (data) => {
  const res = await api.post("/admin/wallet/adjust", data);
  return res.data;
};

export const getAdminAnalytics = async () => {
  const res = await api.get("/admin/analytics");
  return res.data;
};

export const getAdminSystemHealth = async () => {
  const res = await api.get("/admin/system/health");
  return res.data;
};

export const getAdminAuditLogs = async (params = {}) => {
  const res = await api.get("/admin/audit-logs", { params });
  return res.data;
};
