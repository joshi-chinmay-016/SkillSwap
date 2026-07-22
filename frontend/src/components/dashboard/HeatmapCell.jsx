import React, { memo } from "react";
import { LEVEL_CLASSES, formatTooltipDate } from "../../utils/heatmapUtils";

/**
 * HeatmapCell Component (Day 55 Part B3)
 *
 * Renders an individual 11px x 11px contribution calendar cell with:
 * - Color intensity level (0-4)
 * - Accessible keyboard navigation & ARIA attributes
 * - Hover & focus scale interaction
 * - Memoization for high grid performance
 */
function HeatmapCell({
  dateStr,
  count = 0,
  level = 0,
  onHover,
  onLeave,
  onFocus,
  className = "",
}) {
  const formattedDate = formatTooltipDate(dateStr);
  const countText = count === 0 ? "No learning activity" : `${count} ${count === 1 ? "learning activity" : "learning activities"}`;
  const label = `${countText} on ${formattedDate}`;

  const levelClass = LEVEL_CLASSES[level] || LEVEL_CLASSES[0];

  const handleMouseEnter = (e) => {
    if (onHover) {
      const rect = e.currentTarget.getBoundingClientRect();
      onHover({ dateStr, count, formattedDate, countText, rect });
    }
  };

  const handleFocus = (e) => {
    if (onFocus) {
      const rect = e.currentTarget.getBoundingClientRect();
      onFocus({ dateStr, count, formattedDate, countText, rect });
    }
  };

  return (
    <div
      role="gridcell"
      tabIndex={0}
      data-date={dateStr}
      data-count={count}
      data-level={level}
      aria-label={label}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={onLeave}
      onFocus={handleFocus}
      onBlur={onLeave}
      className={`
        w-[11px] h-[11px] rounded-[2px] cursor-pointer
        transition-all duration-150 ease-out
        hover:scale-125 hover:z-20 hover:shadow-xs
        focus:scale-125 focus:z-20 focus:outline-none focus:ring-1 focus:ring-accent
        ${levelClass}
        ${className}
      `}
    />
  );
}

export default memo(HeatmapCell);
