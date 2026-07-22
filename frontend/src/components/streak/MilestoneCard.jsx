// src/components/streak/MilestoneCard.jsx
import React from "react";
import Card from "../common/Card";

/**
 * Component displaying current and next learning milestones.
 * @param {Object} props
 * @param {{name:string, threshold:number}|null} props.currentMilestone
 * @param {{name:string, threshold:number}} props.nextMilestone
 * @param {number} props.remainingDays
 * @param {number} props.progressPercentage
 */
export default function MilestoneCard({
  currentMilestone,
  nextMilestone,
  remainingDays,
  progressPercentage,
}) {
  return (
    <Card title="Learning Milestones" className="h-auto">
      <dl className="grid gap-2 text-sm text-text">
        {/* Current Milestone */}
        <div className="flex items-center justify-between">
          <dt className="font-medium">Current Milestone</dt>
          <dd className="text-accent">
            {currentMilestone ? (
              <span>
                {currentMilestone.name} ({currentMilestone.threshold} days)
              </span>
            ) : (
              <span className="italic text-text-secondary">
                No milestone reached yet
              </span>
            )}
          </dd>
        </div>
        {/* Next Milestone */}
        <div className="flex items-center justify-between">
          <dt className="font-medium">Next Milestone</dt>
          <dd className="text-accent">
            {nextMilestone.name} ({nextMilestone.threshold} days)
          </dd>
        </div>
        {/* Progress */}
        <div className="flex items-center gap-2 mt-2">
          <div className="flex-1 h-2 bg-border/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-accent transition-width duration-300"
              style={{ width: `${progressPercentage}%` }}
              aria-valuenow={progressPercentage}
              aria-valuemin="0"
              aria-valuemax="100"
              role="progressbar"
            ></div>
          </div>
          <span className="text-xs text-text-secondary whitespace-nowrap">
            {remainingDays} days left
          </span>
        </div>
      </dl>
    </Card>
  );
}
