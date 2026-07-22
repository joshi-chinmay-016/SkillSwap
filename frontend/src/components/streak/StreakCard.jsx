// src/components/streak/StreakCard.jsx
import React from "react";
import { useStreak } from "../../hooks/useStreak";
import Card from "../common/Card";
import { RefreshCw } from "lucide-react";

/**
 * Dashboard card displaying learning streak analytics.
 */
export default function StreakCard() {
  const { data, isLoading, isError, refetch } = useStreak();

  if (isLoading) {
    return (
      <Card title="Learning Streak" className="h-48">
        <div className="flex flex-col gap-2 py-4">
          <div className="h-6 w-1/3 bg-border/40 animate-pulse rounded" />
          <div className="h-6 w-1/2 bg-border/40 animate-pulse rounded" />
          <div className="h-6 w-1/4 bg-border/40 animate-pulse rounded" />
        </div>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card title="Learning Streak" className="h-48">
        <div className="flex flex-col items-center justify-center h-full text-center text-text-secondary">
          <p className="mb-2">Unable to load streak.</p>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1 text-accent hover:underline"
          >
            <RefreshCw size={16} /> Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!data || data.total_active_days === 0) {
    return (
      <Card title="Learning Streak" className="h-48">
        <div className="flex flex-col items-center justify-center h-full text-center text-text-secondary">
          <p className="mb-2">Start your first learning journey to begin your streak.</p>
        </div>
      </Card>
    );
  }

  const {
    current_streak,
    longest_streak,
    consistency_score,
    // other fields are available if needed
  } = data;

  return (
    <Card title="Learning Streak" className="h-48">
      <dl className="grid gap-2 text-sm text-text">
        <div className="flex items-center justify-between">
          <dt className="font-medium">Current Streak</dt>
          <dd className="flex items-center gap-1 text-xl font-bold text-accent">
            <span role="img" aria-label="fire">🔥</span>
            {current_streak} Days
          </dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="font-medium">Longest Streak</dt>
          <dd>{longest_streak} Days</dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="font-medium">Consistency</dt>
          <dd>{consistency_score}%</dd>
        </div>
      </dl>
    </Card>
  );
}
