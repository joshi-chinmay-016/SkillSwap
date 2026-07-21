import React from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Skeleton from "../common/Skeleton";
import useHeatmap from "../../hooks/useHeatmap";
import ContributionGrid from "./ContributionGrid";
import { Activity, AlertCircle, RefreshCw } from "lucide-react";

/**
 * HeatmapCard Component (Day 55 Part B2)
 *
 * Responsibilities:
 * - Fetches aggregated learning activity heatmap via `useHeatmap()`
 * - Handles loading, error (with retry), and empty states
 * - Renders ContributionGrid calendar when activity data is available
 */
export default function HeatmapCard({ className = "" }) {
  const { data, isLoading, isError, refetch } = useHeatmap();

  const activityList = data?.activity || [];
  const totalActivities = data?.total_activities ?? 0;
  const totalActiveDays = data?.total_active_days ?? 0;

  return (
    <Card
      title="Learning Activity"
      subtitle="Your daily activity heatmap"
      className={`min-h-[180px] flex flex-col justify-between ${className}`}
    >
      {/* 1. Loading State */}
      {isLoading && (
        <div
          role="status"
          aria-live="polite"
          className="py-4 flex flex-col gap-3 justify-center items-center h-full min-h-[110px]"
        >
          <div className="flex items-center gap-2 text-text-secondary text-sm">
            <RefreshCw size={16} className="animate-spin text-accent" />
            <span>Loading learning activity...</span>
          </div>
          <Skeleton variant="rectangular" className="w-full h-24 mt-2 rounded-lg" />
        </div>
      )}

      {/* 2. Error State */}
      {!isLoading && isError && (
        <div
          role="alert"
          className="py-4 flex flex-col items-center justify-center text-center gap-3 min-h-[110px]"
        >
          <div className="flex items-center gap-2 text-red-500 text-sm font-medium">
            <AlertCircle size={18} />
            <span>Unable to load learning activity.</span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => refetch()}
            className="flex items-center gap-1.5 mt-1 text-xs"
            aria-label="Retry loading learning activity"
          >
            <RefreshCw size={12} />
            Retry
          </Button>
        </div>
      )}

      {/* 3. Empty State (No Data from Backend) */}
      {!isLoading && !isError && activityList.length === 0 && (
        <div className="py-6 flex flex-col items-center justify-center text-center gap-2 min-h-[110px]">
          <div className="w-9 h-9 rounded-full bg-bg-alt flex items-center justify-center text-text-secondary border border-border">
            <Activity size={18} />
          </div>
          <div>
            <p className="font-semibold text-sm text-text">No learning activity yet.</p>
            <p className="text-xs text-text-secondary mt-1 max-w-sm">
              Complete your first learning task to begin building your contribution graph.
            </p>
          </div>
        </div>
      )}

      {/* 4. Loaded State: Summary Header & 365-Day Contribution Grid */}
      {!isLoading && !isError && activityList.length > 0 && (
        <div className="py-2 flex flex-col gap-3">
          <div className="flex items-center justify-between bg-bg p-3 rounded-lg border border-border text-xs">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-accent/10 text-accent flex items-center justify-center font-bold">
                <Activity size={14} />
              </div>
              <div className="text-left">
                <span className="font-bold text-text text-sm">{totalActivities}</span>
                <span className="text-text-secondary ml-1">total activities</span>
              </div>
            </div>
            <div className="text-right text-text-secondary">
              <span className="font-bold text-text">{totalActiveDays}</span> active {totalActiveDays === 1 ? "day" : "days"}
            </div>
          </div>

          {/* 365-Day GitHub Contribution Calendar Grid */}
          <ContributionGrid activity={activityList} />
        </div>
      )}
    </Card>
  );
}
