import React, { useState, useMemo, useCallback, memo } from "react";
import HeatmapCell from "./HeatmapCell";
import Legend from "./Legend";
import {
  mapActivity,
  generateCalendar,
  groupWeeks,
  getMonthLabels,
} from "../../utils/heatmapUtils";

/**
 * ContributionGrid Component (Day 55 Part B3)
 *
 * Responsibilities:
 * - Transforms raw activity array into 365-day contribution calendar (memoized)
 * - Renders 7-row GitHub-style week columns with color levels
 * - Displays month header labels and day labels (Mon, Wed, Fri)
 * - Manages interactive hover/focus tooltips smoothly
 * - Renders contribution level legend
 * - Enables horizontal scrolling on tablet/mobile screens
 */
function ContributionGrid({ activity = [], className = "" }) {
  const [tooltip, setTooltip] = useState(null);

  const { weeks, monthLabels } = useMemo(() => {
    const activityMap = mapActivity(activity);
    const calendarDays = generateCalendar(activityMap, 365);
    const weeksList = groupWeeks(calendarDays);
    const labels = getMonthLabels(weeksList);
    return { weeks: weeksList, monthLabels: labels };
  }, [activity]);

  // Day label names for GitHub 7-row layout
  const dayLabels = ["", "Mon", "", "Wed", "", "Fri", ""];

  const handleCellHover = useCallback((info) => {
    setTooltip(info);
  }, []);

  const handleCellLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  return (
    <div className={`relative flex flex-col gap-3 w-full select-none py-1 ${className}`}>
      {/* Scrollable Heatmap Container */}
      <div className="w-full overflow-x-auto relative pb-1">
        <div className="inline-flex flex-col gap-1 min-w-max">
          {/* Month Labels Header Row */}
          <div className="flex text-[10px] text-text-secondary h-4 pl-8">
            <div className="relative w-full flex">
              {monthLabels.map(({ weekIndex, label }) => (
                <div
                  key={`${weekIndex}-${label}`}
                  className="absolute"
                  style={{ left: `${weekIndex * 14}px` }}
                >
                  {label}
                </div>
              ))}
            </div>
          </div>

          {/* Main Grid: Day Labels + Week Columns */}
          <div className="flex flex-row items-start gap-2">
            {/* Day Labels Column (Mon, Wed, Fri) */}
            <div className="flex flex-col gap-[3px] text-[9px] text-text-secondary h-[95px] justify-between pt-[1px] pr-1">
              {dayLabels.map((dayName, idx) => (
                <span key={idx} className="h-[11px] leading-[11px] text-right font-medium">
                  {dayName}
                </span>
              ))}
            </div>

            {/* Week Columns Grid */}
            <div
              role="grid"
              aria-label="Contribution activity calendar"
              className="flex flex-row gap-[3px] relative"
            >
              {weeks.map((week, weekIdx) => (
                <div
                  key={weekIdx}
                  role="row"
                  className="flex flex-col gap-[3px]"
                >
                  {week.map((day) => (
                    <HeatmapCell
                      key={day.dateStr}
                      dateStr={day.dateStr}
                      count={day.count}
                      level={day.level}
                      date={day.date}
                      onHover={handleCellHover}
                      onFocus={handleCellHover}
                      onLeave={handleCellLeave}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Dynamic Tooltip Overlay */}
        {tooltip && tooltip.rect && (
          <div
            role="tooltip"
            aria-live="polite"
            className="fixed z-50 pointer-events-none px-2.5 py-1.5 bg-bg-alt border border-border rounded-md shadow-md text-xs text-text transition-opacity duration-150 transform -translate-x-1/2 -translate-y-full mb-2"
            style={{
              top: `${tooltip.rect.top - 6}px`,
              left: `${tooltip.rect.left + tooltip.rect.width / 2}px`,
            }}
          >
            <span className="font-semibold">{tooltip.countText}</span>
            <span className="text-text-secondary ml-1 font-normal">on {tooltip.formattedDate}</span>
          </div>
        )}
      </div>

      {/* Heatmap Footer: Legend */}
      <div className="flex items-center justify-between text-xs pt-1 border-t border-border/50">
        <span className="text-[11px] text-text-secondary">
          Learn more about how activity is recorded
        </span>
        <Legend />
      </div>
    </div>
  );
}

export default memo(ContributionGrid);
