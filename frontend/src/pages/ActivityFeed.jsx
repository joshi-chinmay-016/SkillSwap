import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Skeleton from "../components/common/Skeleton";
import {
  Activity,
  CheckCircle,
  Award,
  Trophy,
  Filter,
  ChevronLeft,
  ChevronRight,
  Clock,
  BookOpen,
  Sparkles,
  Compass,
} from "lucide-react";

const ACTIVITY_TYPES = [
  { value: "", label: "All Activities" },
  { value: "task_completed", label: "Tasks Completed" },
  { value: "milestone_completed", label: "Milestones Completed" },
  { value: "journey_completed", label: "Journeys Completed" },
];

const ACTIVITY_CONFIG = {
  task_completed: {
    icon: CheckCircle,
    color: "text-accent",
    bg: "bg-accent/10",
    border: "border-accent/20",
    label: "Task Completed",
    description: (data) => {
      if (data?.milestone_id) {
        return `Completed a task in your learning journey`;
      }
      return "Completed a learning task";
    },
  },
  milestone_completed: {
    icon: Award,
    color: "text-success",
    bg: "bg-success/10",
    border: "border-success/20",
    label: "Milestone Completed",
    description: () => "Completed a weekly milestone — great progress!",
  },
  journey_completed: {
    icon: Trophy,
    color: "text-warning",
    bg: "bg-warning/10",
    border: "border-warning/20",
    label: "Journey Completed",
    description: () => "Completed an entire learning journey — outstanding! 🎉",
  },
};

function getRelativeTime(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

const PAGE_SIZE = 15;

export default function ActivityFeed() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [activityType, setActivityType] = useState("");

  const {
    data,
    isLoading,
    error,
    isFetching,
  } = useQuery({
    queryKey: ["activities", page, activityType],
    queryFn: async () => {
      const params = { page, size: PAGE_SIZE };
      if (activityType) params.activity_type = activityType;
      const res = await api.get("/learning-activities/me", { params });
      return res.data;
    },
    keepPreviousData: true,
  });

  const activities = data?.activities || [];
  const total = data?.total || 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <Skeleton variant="text" width="220px" height="28px" />
          <Skeleton variant="text" width="320px" height="16px" />
        </div>
        <div className="flex flex-col gap-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="flex items-start gap-4 p-4 border border-border rounded-lg bg-bg"
            >
              <Skeleton variant="circular" width="36px" height="36px" />
              <div className="flex-1 space-y-2">
                <Skeleton variant="text" width="40%" height="16px" />
                <Skeleton variant="text" width="70%" height="12px" />
              </div>
              <Skeleton variant="text" width="50px" height="12px" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-md mx-auto mt-12">
        <Card className="text-center py-8">
          <div className="p-3 bg-danger/10 text-danger rounded-full w-fit mx-auto mb-4">
            <Activity size={32} />
          </div>
          <h2 className="text-lg font-bold text-text">
            Failed to load activities
          </h2>
          <p className="text-sm text-text-secondary mt-2 px-4">
            We couldn't retrieve your learning activity history. Please try
            again later.
          </p>
          <div className="mt-6">
            <Button
              variant="primary"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text flex items-center gap-2.5">
            <div className="p-2 bg-accent/10 text-accent rounded-lg">
              <Activity size={20} />
            </div>
            Learning Activity
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Your real learning actions — tasks, milestones, and journeys you've
            completed.
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-text-secondary" />
          <select
            value={activityType}
            onChange={(e) => {
              setActivityType(e.target.value);
              setPage(1);
            }}
            className="text-xs font-medium px-3 py-1.5 rounded-lg border border-border bg-bg text-text
                       focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent/40
                       cursor-pointer transition-colors"
          >
            {ACTIVITY_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats Bar */}
      {total > 0 && (
        <div className="flex items-center gap-4 px-4 py-3 bg-bg border border-border rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            <span className="text-xs font-semibold text-text">
              {total} {total === 1 ? "activity" : "activities"}
            </span>
          </div>
          <div className="h-3 w-px bg-border" />
          <span className="text-xs text-text-secondary">
            Page {page} of {totalPages}
          </span>
        </div>
      )}

      {/* Activity Timeline */}
      {activities.length === 0 ? (
        <Card className="text-center py-12">
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
                <Sparkles size={28} className="text-accent" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-bg-alt border-2 border-border flex items-center justify-center">
                <BookOpen size={12} className="text-text-secondary" />
              </div>
            </div>
            <div>
              <h3 className="font-bold text-text text-base">
                No learning activity yet
              </h3>
              <p className="text-sm text-text-secondary mt-1 max-w-sm mx-auto">
                Complete tasks in your Learning Journey to start building your
                activity history. Every real action is recorded here.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/journey/roadmap")}
            >
              <Compass size={14} className="mr-1.5" />
              Start a Learning Journey
            </Button>
          </div>
        </Card>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[22px] top-6 bottom-6 w-px bg-border" />

          <div className="flex flex-col gap-1">
            {activities.map((activity, index) => {
              const config =
                ACTIVITY_CONFIG[activity.activity_type] || ACTIVITY_CONFIG.task_completed;
              const IconComponent = config.icon;

              return (
                <div
                  key={activity.id}
                  className="relative flex items-start gap-4 pl-1 py-3 group"
                >
                  {/* Timeline dot */}
                  <div
                    className={`
                      relative z-10 flex-shrink-0 w-[36px] h-[36px] rounded-xl
                      flex items-center justify-center border
                      ${config.bg} ${config.border}
                      group-hover:scale-110 transition-transform duration-200
                    `}
                  >
                    <IconComponent size={16} className={config.color} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 pt-0.5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${config.bg} ${config.color} ${config.border}`}
                        >
                          {config.label}
                        </span>
                        <p className="text-sm text-text-secondary mt-1.5 leading-relaxed">
                          {config.description(activity.activity_data)}
                        </p>
                      </div>

                      <span className="flex-shrink-0 text-[11px] text-text-secondary font-medium flex items-center gap-1 mt-0.5">
                        <Clock size={11} />
                        {getRelativeTime(activity.created_at)}
                      </span>
                    </div>

                    {/* Context metadata */}
                    {activity.activity_data &&
                      Object.keys(activity.activity_data).length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {activity.activity_data.journey_id && (
                            <button
                              onClick={() =>
                                navigate(
                                  `/journey/${activity.activity_data.journey_id}`
                                )
                              }
                              className="inline-flex items-center gap-1 text-[10px] font-medium text-accent
                                         bg-accent/5 border border-accent/10 px-2 py-0.5 rounded-md
                                         hover:bg-accent/10 transition-colors cursor-pointer"
                            >
                              <Compass size={10} />
                              View Journey
                            </button>
                          )}
                        </div>
                      )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <Button
            variant="outline"
            size="xs"
            disabled={page <= 1 || isFetching}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft size={14} />
            Previous
          </Button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  disabled={isFetching}
                  className={`
                    w-8 h-8 rounded-lg text-xs font-semibold transition-all cursor-pointer
                    ${
                      pageNum === page
                        ? "bg-accent text-white shadow-sm"
                        : "text-text-secondary hover:bg-bg-alt hover:text-text border border-transparent hover:border-border"
                    }
                  `}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <Button
            variant="outline"
            size="xs"
            disabled={page >= totalPages || isFetching}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
            <ChevronRight size={14} />
          </Button>
        </div>
      )}

      {/* Fetching overlay indicator */}
      {isFetching && !isLoading && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2 bg-bg border border-border rounded-lg shadow-md flex items-center gap-2 text-xs font-medium text-text-secondary animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="w-3 h-3 rounded-full border-2 border-accent/40 border-t-accent animate-spin" />
          Loading...
        </div>
      )}
    </div>
  );
}
