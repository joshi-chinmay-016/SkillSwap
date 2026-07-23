import React, { useState } from "react";
import {
  Activity,
  Zap,
  Calendar,
  Flame,
  BarChart2,
  AlertCircle,
  RefreshCw,
  Clock,
  Sparkles,
} from "lucide-react";
import { useAnalytics } from "../../hooks/useAnalytics";
import SummaryCard from "./SummaryCard";
import TrendCard from "./TrendCard";
import ActivityCharts from "./ActivityCharts";
import AiInsightCard from "./AiInsightCard";
import ExportAnalytics from "./ExportAnalytics";

export default function AnalyticsSection({ title = "Learning Intelligence & Analytics" }) {
  const [timeFilter, setTimeFilter] = useState("all");
  const { data: analytics, isLoading, isError, error, refetch } = useAnalytics(timeFilter);

  // Time Filter definitions
  const filters = [
    { key: "7d", label: "Last 7 Days" },
    { key: "30d", label: "Last 30 Days" },
    { key: "90d", label: "Last 90 Days" },
    { key: "all", label: "All Time" },
  ];

  // Check if data is completely empty (new user)
  const isEmptyState =
    analytics &&
    (!analytics.summary || analytics.summary.total_activities === 0) &&
    (!analytics.weekly_activity || Object.keys(analytics.weekly_activity).length === 0);

  return (
    <section aria-label="Learning Analytics Section" className="flex flex-col gap-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-card border border-border p-5 rounded-xl shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
            <BarChart2 className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground tracking-tight m-0">
              {title}
            </h2>
            <p className="text-xs text-muted-foreground m-0">
              Real-time insights and engagement metrics
            </p>
          </div>
        </div>

        {/* Action Controls: Time Filter & Export */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Time Filter Pills */}
          <div className="inline-flex items-center p-1 bg-muted rounded-lg border border-border/50 text-xs">
            {filters.map((f) => (
              <button
                key={f.key}
                onClick={() => setTimeFilter(f.key)}
                className={`px-2.5 py-1 font-semibold rounded-md transition-all ${
                  timeFilter === f.key
                    ? "bg-card text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <ExportAnalytics analytics={analytics} />
        </div>
      </div>

      {/* Loading Skeleton State */}
      {isLoading && (
        <div className="flex flex-col gap-6 animate-pulse" role="status" aria-label="Loading analytics">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-muted rounded-xl" />
            ))}
          </div>
          <div className="h-80 bg-muted rounded-xl" />
        </div>
      )}

      {/* Error State */}
      {isError && !isLoading && (
        <div
          role="alert"
          className="bg-destructive/10 border border-destructive/20 rounded-xl p-6 flex flex-col items-center justify-center text-center gap-3"
        >
          <AlertCircle className="w-8 h-8 text-destructive" />
          <div>
            <h3 className="text-sm font-bold text-foreground m-0">
              Unable to load analytics
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              {error?.response?.data?.detail || error?.message || "An unexpected error occurred while fetching analytics data."}
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      )}

      {/* Empty State for Brand New User */}
      {isEmptyState && !isLoading && !isError && (
        <div className="bg-card border border-border rounded-xl p-8 flex flex-col items-center justify-center text-center gap-4 shadow-xs">
          <div className="p-4 rounded-full bg-primary/10 text-primary">
            <Sparkles className="w-8 h-8" />
          </div>
          <div className="max-w-md">
            <h3 className="text-base font-bold text-foreground m-0">
              Start learning to unlock analytics
            </h3>
            <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
              Complete practice sessions, join skill swaps, or log learning activities to track your velocity, streaks, and peak performance days here!
            </p>
          </div>
        </div>
      )}

      {/* Main Analytics Content */}
      {!isLoading && !isError && !isEmptyState && analytics && (
        <div className="flex flex-col gap-6">
          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <SummaryCard
              title="Total Activities"
              value={analytics.summary?.total_activities}
              icon={Activity}
              subtext={`${analytics.summary?.total_active_days || 0} active days`}
            />

            <SummaryCard
              title="Current Streak"
              value={analytics.summary?.current_streak ? `${analytics.summary.current_streak} days` : "0 days"}
              icon={Flame}
              subtext={`Best: ${analytics.summary?.longest_streak || 0} days`}
            />

            <SummaryCard
              title="Learning Velocity"
              value={`${analytics.learning_velocity || 0}/day`}
              icon={Zap}
              subtext="30-day average rate"
            />

            <SummaryCard
              title="Most Active Day"
              value={analytics.most_active_day?.day || "N/A"}
              icon={Calendar}
              subtext={
                analytics.most_active_day?.count
                  ? `${analytics.most_active_day.count} activities logged`
                  : "No data yet"
              }
            />

            <TrendCard trendInfo={analytics.learning_trend} />
          </div>

          {/* AI Insights Card */}
          <AiInsightCard analytics={analytics} />

          {/* Interactive Recharts */}
          <ActivityCharts analytics={analytics} />
        </div>
      )}
    </section>
  );
}
