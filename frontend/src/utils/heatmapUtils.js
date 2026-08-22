/**
 * Utility functions for GitHub-style Learning Activity Heatmap calendar generation,
 * level mapping, formatting, and responsiveness.
 */

/**
 * Format a Date object into local YYYY-MM-DD string without timezone shifting.
 * @param {Date} date
 * @returns {string}
 */
export const formatDateKey = (date) => {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
};

/**
 * Format a Date or YYYY-MM-DD string into a user-friendly readable date.
 * Example: "2026-07-20" -> "July 20, 2026"
 * @param {Date|string} dateInput
 * @returns {string}
 */
export const formatTooltipDate = (dateInput) => {
  if (!dateInput) return "";
  let d;
  if (typeof dateInput === "string") {
    const [year, month, day] = dateInput.split("-").map(Number);
    d = new Date(year, month - 1, day);
  } else {
    d = new Date(dateInput);
  }
  return d.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
};

/**
 * Configurable thresholds for activity contribution levels.
 * Level 0: 0
 * Level 1: 1-2
 * Level 2: 3-5
 * Level 3: 6-9
 * Level 4: 10+
 */
export const LEVEL_THRESHOLDS = [
  { min: 0, max: 0, level: 0 },
  { min: 1, max: 2, level: 1 },
  { min: 3, max: 5, level: 2 },
  { min: 6, max: 9, level: 3 },
  { min: 10, max: Infinity, level: 4 },
];

/**
 * Calculate contribution level (0 to 4) based on activity count.
 * @param {number} count
 * @returns {number} Level 0 to 4
 */
export const getContributionLevel = (count = 0) => {
  if (!count || count <= 0) return 0;
  for (const t of LEVEL_THRESHOLDS) {
    if (count >= t.min && count <= t.max) {
      return t.level;
    }
  }
  return 4;
};

/**
 * Tailored Tailwind style classes for each contribution level (0-4).
 * Works seamlessly in both Light Mode and Dark Mode using design tokens.
 */
export const LEVEL_CLASSES = {
  0: "bg-slate-200/80 border border-slate-300/70 hover:border-slate-400 dark:bg-slate-800/80 dark:border-slate-700/80 dark:hover:border-slate-500",
  1: "bg-emerald-500/30 border border-emerald-500/40 hover:border-emerald-500/70 dark:bg-emerald-500/35 dark:border-emerald-500/45",
  2: "bg-emerald-500/60 border border-emerald-500/70 hover:border-emerald-500/90 dark:bg-emerald-500/65 dark:border-emerald-500/75",
  3: "bg-emerald-500/85 border border-emerald-500/90 hover:border-emerald-400 dark:bg-emerald-500/90 dark:border-emerald-400",
  4: "bg-emerald-500 border border-emerald-400 shadow-xs hover:border-emerald-300 dark:bg-emerald-400 dark:border-emerald-300",
};

/**
 * Transform backend activity array into an O(1) lookup Map.
 * @param {Array<{date: string, count: number}>} activityList
 * @returns {Map<string, number>}
 */
export const mapActivity = (activityList = []) => {
  const map = new Map();
  if (Array.isArray(activityList)) {
    for (const item of activityList) {
      if (item && item.date) {
        map.set(item.date, item.count || 0);
      }
    }
  }
  return map;
};

/**
 * Generate an array of calendar day objects for the past N days (default 365),
 * aligned to start on Sunday.
 *
 * @param {Map<string, number>} activityMap
 * @param {number} daysCount
 * @param {Date} [endDate=new Date()]
 * @returns {Array<{date: Date, dateStr: string, count: number, level: number, dayOfWeek: number, month: number, year: number}>}
 */
export const generateCalendar = (activityMap, daysCount = 365, endDate = new Date()) => {
  const today = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate());

  // Calculate start date: 364 days before today
  const start = new Date(today);
  start.setDate(start.getDate() - (daysCount - 1));

  // Align back to the preceding Sunday so week columns start cleanly on Sunday (day 0)
  const startDayOfWeek = start.getDay();
  start.setDate(start.getDate() - startDayOfWeek);

  const days = [];
  const current = new Date(start);

  while (current <= today) {
    const dateStr = formatDateKey(current);
    const count = activityMap.get(dateStr) || 0;
    const level = getContributionLevel(count);

    days.push({
      date: new Date(current),
      dateStr,
      count,
      level,
      dayOfWeek: current.getDay(),
      month: current.getMonth(),
      year: current.getFullYear(),
    });

    current.setDate(current.getDate() + 1);
  }

  return days;
};

/**
 * Group flat calendar days array into 7-day week columns (Sun-Sat).
 * @param {Array} calendarDays
 * @returns {Array<Array>} Array of weeks
 */
export const groupWeeks = (calendarDays) => {
  const weeks = [];
  let currentWeek = [];

  for (const day of calendarDays) {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }

  if (currentWeek.length > 0) {
    weeks.push(currentWeek);
  }

  return weeks;
};

/**
 * Generate month label metadata mapped to week column indices.
 * @param {Array<Array>} weeks
 * @returns {Array<{weekIndex: number, label: string}>}
 */
export const getMonthLabels = (weeks) => {
  const labels = [];
  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  ];
  let lastMonth = -1;

  weeks.forEach((week, weekIndex) => {
    // Find the first day in this week with a new month
    const firstDayWithNewMonth = week.find((day) => day.month !== lastMonth);
    if (firstDayWithNewMonth && firstDayWithNewMonth.month !== lastMonth) {
      lastMonth = firstDayWithNewMonth.month;
      labels.push({
        weekIndex,
        label: monthNames[firstDayWithNewMonth.month],
      });
    }
  });

  return labels;
};
