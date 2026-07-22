// src/types/streak.js
/**
 * @typedef {Object} MilestoneInfo
 * @property {string} name - Milestone name
 * @property {number} threshold - Days required for the milestone
 */

/**
 * @typedef {Object} StreakResponse
 * @property {number} current_streak - Current active streak in days
 * @property {number} longest_streak - Longest streak recorded
 * @property {number} total_active_days - Total unique active days
 * @property {string|null} last_active_date - ISO date string of last activity
 * @property {number} consistency_score - Consistency percentage
 * @property {MilestoneInfo|null} current_milestone - Current milestone info
 * @property {MilestoneInfo} next_milestone - Next milestone info
 * @property {number} remaining_days - Days remaining to reach next milestone
 * @property {number} progress_percentage - Progress towards next milestone
 */

export {};
