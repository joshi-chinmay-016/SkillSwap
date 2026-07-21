import React, { memo } from "react";
import { LEVEL_CLASSES } from "../../utils/heatmapUtils";

/**
 * Heatmap Legend Component (Day 55 Part B3)
 *
 * Renders the level indicator legend (Less -> Level 0..4 -> More)
 * matching the contribution graph colors.
 */

const levels = [0, 1, 2, 3, 4];

function Legend({ className = "" }) {
  return (
    <div
      className={`flex items-center gap-1.5 text-[11px] text-text-secondary ${className}`}
      aria-label="Heatmap contribution legend"
    >
      <span>Less</span>
      <div className="flex items-center gap-[3px]">
        {levels.map((lvl) => (
          <div
            key={lvl}
            className={`w-[11px] h-[11px] rounded-[2px] ${LEVEL_CLASSES[lvl]}`}
            title={`Level ${lvl}`}
            aria-label={`Level ${lvl} activity indicator`}
          />
        ))}
      </div>
      <span>More</span>
    </div>
  );
}

export default memo(Legend);
