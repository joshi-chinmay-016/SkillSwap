import React from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Skeleton from "../common/Skeleton";
import useHeatmap from "../../hooks/useHeatmap";
import ContributionGrid from "./ContributionGrid";
import { Activity, AlertCircle, RefreshCw, Calendar } from "lucide-react";

/**
 * HeatmapCard Component
 *
 * Responsibilities:
 * - Fetches authenticated user's real daily activity heatmap via `useHeatmap()`
 * - Always displays the authoritative 365-day GitHub-style Contribution Grid
 * - Handles loading, error (with retry), and shows true totals
 */
export default function HeatmapCard({ className = "" }) {
  const { data, isLoading, isError, refetch } = useHeatmap();

  const activityList = data?.activity || [];
  const totalActivities = data?.total_activities ?? 0;
  const totalActiveDays = data?.total_active_days ?? 0;

  return (
    <Card
      title="Learning Activity & Daily Contributions"
      subtitle="Your personal 365-day skill progression heatmap"
      className={`min-h-[180px] flex flex-col justify-between text-left ${className}`}
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
            <span>Loading personal learning activity...</span>
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

      {/* 3. Loaded State: Summary Header & 365-Day Contribution Grid */}
      {!isLoading && !isError && (
        <div className="py-2 flex flex-col gap-3">
          <div className="flex items-center justify-between bg-bg p-3 rounded-xl border border-border text-xs">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-accent/10 text-accent flex items-center justify-center font-bold">
                <Activity size={16} />
              </div>
              <div className="text-left">
                <span className="font-extrabold text-text text-sm">{totalActivities}</span>
                <span className="text-text-secondary ml-1">total activities logged</span>
              </div>
            </div>
            <div className="text-right text-text-secondary">
              <span className="font-extrabold text-text">{totalActiveDays}</span> active {totalActiveDays === 1 ? "day" : "days"} (last 365 days)
            </div>
          </div>

          {/* 365-Day Contribution Calendar Grid */}
          <ContributionGrid activity={activityList} />
        </div>
      )}
    </Card>
  );
}
