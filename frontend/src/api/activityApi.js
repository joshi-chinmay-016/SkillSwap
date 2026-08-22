import api from "../services/api";

/**
 * @typedef {Object} ActivityItem
 * @property {string} date - ISO date string (YYYY-MM-DD)
 * @property {number} count - Activity count for the date
 */

/**
 * @typedef {Object} HeatmapResponse
 * @property {string} start_date - Start date of the range (YYYY-MM-DD)
 * @property {string} end_date - End date of the range (YYYY-MM-DD)
 * @property {number} total_active_days - Total unique active days
 * @property {number} total_activities - Total count of activities
 * @property {ActivityItem[]} activity - Aggregated daily activity list
 */

/**
 * Fetch aggregated learning activity heatmap data for the authenticated user.
 * The backend endpoint is protected; authentication token is added via the Axios interceptor.
 *
 * @returns {Promise<HeatmapResponse>} Resolves with the heatmap response object.
 */
export const fetchHeatmap = async (timezoneOrContext) => {
  const tz =
    typeof timezoneOrContext === "string" && timezoneOrContext
      ? timezoneOrContext
      : typeof Intl !== "undefined" && Intl.DateTimeFormat
      ? Intl.DateTimeFormat().resolvedOptions().timeZone
      : "UTC";
  const response = await api.get("/activities/heatmap", {
    params: { timezone: tz },
  });
  return response.data;
};

// Export alias for compatibility
export const getHeatmap = fetchHeatmap;

export default {
  fetchHeatmap,
  getHeatmap,
};
