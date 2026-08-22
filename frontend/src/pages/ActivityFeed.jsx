import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Skeleton from "../components/common/Skeleton";
import SectionHeader from "../components/common/SectionHeader";
import EmptyState from "../components/common/EmptyState";
import PageTransition from "../components/common/PageTransition";
import { PushPin } from "../components/common/PinnedCard";
import { MarkerHighlight, HandDrawnNote } from "../components/common/HandwrittenAnnotation";
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
  { value: "session_completed", label: "Sessions Completed" },
];

const ACTIVITY_CONFIG = {
  task_completed: {
    icon: CheckCircle,
    color: "text-accent",
    bg: "bg-accent/10",
    border: "border-accent/20",
    label: "Task Completed",
    description: (data) => data?.task_title || data?.title || "Completed a task in your learning roadmap",
  },
  milestone_completed: {
    icon: Award,
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    label: "Milestone Completed",
    description: (data) => (data?.milestone_topic || data?.title) ? `Completed: ${data.milestone_topic || data.title}` : "Completed a weekly milestone — outstanding progress!",
  },
  journey_completed: {
    icon: Trophy,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    label: "Journey Completed",
    description: (data) => data?.title ? `Finished Journey: ${data.title}` : "Completed an entire learning journey — fantastic achievement! 🎉",
  },
  session_completed: {
    icon: Sparkles,
    color: "text-purple-500",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    label: "Session Completed",
    description: (data) => data?.title || "Completed a live 1-on-1 peer session",
  },
};

function formatTimestamp(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

export default function ActivityFeed() {
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["learning-activities", selectedType, page],
    queryFn: async () => {
      const params = { page, size: pageSize };
      if (selectedType) params.activity_type = selectedType;
      const res = await api.get("/learning-activities/me", { params });
      return res.data;
    },
  });

  const activities = data?.activities || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize) || 1;

  const handleFilterChange = (type) => {
    setSelectedType(type);
    setPage(1);
  };

  return (
    <PageTransition className="space-y-8 text-left max-w-4xl mx-auto">
      {/* Section Header */}
      <SectionHeader
        badge="Progress History"
        badgeIcon={Activity}
        handwrittenNote="📌 Live Study Stream"
        title="Learning Activity Feed"
        subtitle="Track every milestone, roadmap task, and completed journey across your peer learning timeline."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/journey/roadmap")}
            leftIcon={Compass}
            className="font-bold"
          >
            Go to Roadmap 📌
          </Button>
        }
      />

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {ACTIVITY_TYPES.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleFilterChange(tab.value)}
            className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all duration-150 cursor-pointer ${
              selectedType === tab.value
                ? "bg-accent text-white shadow-glow"
                : "bg-surface-elevated text-text-secondary hover:text-text border border-border"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Activities Timeline */}
      <div className="relative">
        <Card title="Activity Timeline" subtitle={`${total} total learning events recorded`}>
          <PushPin color="green" className="-top-3 left-8" />

          {isLoading ? (
            <div className="space-y-4 py-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-16 w-full bg-border/40 animate-pulse rounded-2xl" />
              ))}
            </div>
          ) : isError ? (
            <div className="py-8 text-center space-y-3">
              <p className="text-xs text-danger font-semibold">Failed to load activity stream.</p>
              <Button size="xs" variant="outline" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          ) : activities.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No activity records found"
              description={
                selectedType
                  ? "No activities found matching the selected filter."
                  : "Start working on your learning journeys to see activity logged here automatically."
              }
              actionLabel="Start a Roadmap"
              onAction={() => navigate("/journey/roadmap")}
            />
          ) : (
            <div className="space-y-3 pt-2">
              {activities.map((item) => {
                const config = ACTIVITY_CONFIG[item.activity_type] || {
                  icon: Activity,
                  color: "text-text-secondary",
                  bg: "bg-bg-alt",
                  border: "border-border",
                  label: "Learning Action",
                  description: () => "Completed a learning action",
                };
                const Icon = config.icon;

                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-bg border border-border/80 hover:border-accent/40 rounded-2xl flex items-center justify-between gap-4 transition-all shadow-xs"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className={`p-2.5 rounded-xl border ${config.bg} ${config.color} ${config.border} shrink-0`}>
                        <Icon size={18} />
                      </div>
                      <div className="space-y-0.5">
                        <h4 className="font-bold text-xs sm:text-sm text-text">
                          {config.label}
                        </h4>
                        <p className="text-[11px] text-text-secondary">
                          {config.description(item.activity_data)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 text-[11px] text-text-muted shrink-0 font-medium">
                      <Clock size={12} />
                      <span>{formatTimestamp(item.created_at)}</span>
                    </div>
                  </motion.div>
                );
              })}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pt-6 border-t border-border/80 flex items-center justify-between">
                  <Button
                    size="xs"
                    variant="outline"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    leftIcon={ChevronLeft}
                  >
                    Previous
                  </Button>
                  <span className="text-xs font-semibold text-text-secondary">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    size="xs"
                    variant="outline"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    rightIcon={ChevronRight}
                  >
                    Next
                  </Button>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </PageTransition>
  );
}
