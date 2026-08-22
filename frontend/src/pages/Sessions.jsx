import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "motion/react";
import api from "../services/api";
import { startPeerSession, completePeerSession, cancelPeerSession, joinPeerSession } from "../api/sessionApi";
import Button from "../components/common/Button";
import SectionHeader from "../components/common/SectionHeader";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import PageTransition from "../components/common/PageTransition";
import { PushPin } from "../components/common/PinnedCard";
import {
  Calendar,
  Video,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  MessageSquare,
  ArrowRight,
  Sparkles,
  ExternalLink,
  UserCheck,
  CheckCircle2,
  Play,
  Radio,
} from "lucide-react";

export default function Sessions() {
  const [activeTab, setActiveTab] = useState("upcoming");
  const [actionError, setActionError] = useState("");
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Fetch upcoming sessions
  const {
    data: upcoming = [],
    isLoading: isUpcomingLoading,
    isError: isUpcomingError,
    refetch: refetchUpcoming,
  } = useQuery({
    queryKey: ["upcomingSessions"],
    queryFn: async () => {
      const res = await api.get("/sessions/upcoming");
      return res.data;
    },
  });

  // Fetch completed sessions
  const {
    data: completed = [],
    isLoading: isCompletedLoading,
    isError: isCompletedError,
    refetch: refetchCompleted,
  } = useQuery({
    queryKey: ["completedSessions"],
    queryFn: async () => {
      const res = await api.get("/sessions/completed");
      return res.data;
    },
  });

  // Fetch cancelled sessions
  const {
    data: cancelled = [],
    isLoading: isCancelledLoading,
    isError: isCancelledError,
    refetch: refetchCancelled,
  } = useQuery({
    queryKey: ["cancelledSessions"],
    queryFn: async () => {
      const res = await api.get("/sessions/cancelled");
      return res.data;
    },
  });

  // Start session mutation
  const startMutation = useMutation({
    mutationFn: (sessionId) => startPeerSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
      setActionError("");
    },
    onError: (err) => {
      setActionError(err.response?.data?.detail || "Failed to start session.");
    },
  });

  // Complete session mutation
  const completeMutation = useMutation({
    mutationFn: (sessionId) => completePeerSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
      queryClient.invalidateQueries({ queryKey: ["completedSessions"] });
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["learning-activities"] });
      queryClient.invalidateQueries({ queryKey: ["streak"] });
      queryClient.invalidateQueries({ queryKey: ["heatmap"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      setActionError("");
    },
    onError: (err) => {
      setActionError(err.response?.data?.detail || "Failed to mark session as complete.");
    },
  });

  // Cancel session mutation
  const cancelMutation = useMutation({
    mutationFn: (sessionId) => cancelPeerSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
      queryClient.invalidateQueries({ queryKey: ["cancelledSessions"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      setActionError("");
    },
    onError: (err) => {
      setActionError(err.response?.data?.detail || "Failed to cancel session.");
    },
  });

  const handleJoinCall = async (session) => {
    try {
      await joinPeerSession(session.id);
    } catch {
      // Non-blocking
    }
    if (session.meeting_link) {
      window.open(session.meeting_link, "_blank", "noopener,noreferrer");
    }
  };

  const isLoading =
    activeTab === "upcoming"
      ? isUpcomingLoading
      : activeTab === "completed"
      ? isCompletedLoading
      : isCancelledLoading;

  const isError =
    activeTab === "upcoming"
      ? isUpcomingError
      : activeTab === "completed"
      ? isCompletedError
      : isCancelledError;

  const sessionsList =
    activeTab === "upcoming"
      ? upcoming
      : activeTab === "completed"
      ? completed
      : cancelled;

  return (
    <PageTransition className="space-y-8 text-left max-w-6xl mx-auto">
      {/* Section Header */}
      <SectionHeader
        badge="Classroom Desk"
        badgeIcon={Calendar}
        handwrittenNote="📌 Live Study Rooms"
        title="Learning Sessions"
        subtitle="Manage your 1-on-1 peer exchange sessions, join live rooms, and review completed notes."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate("/mentors")}
            rightIcon={ArrowRight}
            className="shadow-glow font-bold"
          >
            Book New Session 📌
          </Button>
        }
      />

      {/* Error Alert */}
      {actionError && (
        <div className="p-3.5 text-xs bg-danger/10 border border-danger/20 text-danger rounded-2xl font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0" />
            <span>{actionError}</span>
          </div>
          <button
            type="button"
            onClick={() => setActionError("")}
            className="font-bold underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs Switcher */}
      <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-surface-elevated border border-border w-fit shadow-xs">
        <button
          type="button"
          onClick={() => {
            setActiveTab("upcoming");
            setActionError("");
          }}
          className={`px-5 py-2 text-xs font-bold rounded-xl transition-all duration-200 cursor-pointer ${
            activeTab === "upcoming"
              ? "bg-accent text-white shadow-glow"
              : "text-text-secondary hover:text-text"
          }`}
        >
          Upcoming / Active ({upcoming.length})
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("completed");
            setActionError("");
          }}
          className={`px-5 py-2 text-xs font-bold rounded-xl transition-all duration-200 cursor-pointer ${
            activeTab === "completed"
              ? "bg-accent text-white shadow-glow"
              : "text-text-secondary hover:text-text"
          }`}
        >
          Completed ({completed.length})
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("cancelled");
            setActionError("");
          }}
          className={`px-5 py-2 text-xs font-bold rounded-xl transition-all duration-200 cursor-pointer ${
            activeTab === "cancelled"
              ? "bg-accent text-white shadow-glow"
              : "text-text-secondary hover:text-text"
          }`}
        >
          Cancelled ({cancelled.length})
        </button>
      </div>

      {/* Sessions Content */}
      <div>
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 w-full bg-border/40 animate-pulse rounded-2xl" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState
            title="Failed to load sessions"
            message="Could not load your session history. Please try again."
            onRetry={() => (activeTab === "upcoming" ? refetchUpcoming() : refetchCompleted())}
          />
        ) : sessionsList.length === 0 ? (
          <EmptyState
            icon={Calendar}
            title={
              activeTab === "upcoming"
                ? "You don't have any upcoming peer-learning sessions."
                : "No completed sessions yet"
            }
            description={
              activeTab === "upcoming"
                ? "Browse our verified student mentors to schedule your next 1-on-1 peer exchange session."
                : "You haven't completed any sessions yet. Once you complete a session with a peer, it will appear here."
            }
            actionLabel={activeTab === "upcoming" ? "Find a Mentor" : undefined}
            onAction={() => navigate("/mentors")}
          />
        ) : (
          <div className="space-y-6">
            {sessionsList.map((session, index) => {
              const pinColors = ["cyan", "yellow", "purple", "green", "red"];
              const selectedColor = pinColors[index % pinColors.length];
              const isLive = session.status === "in_progress";
              const isScheduled = session.status === "scheduled";

              return (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`relative p-6 sm:p-7 bg-card-bg border rounded-3xl shadow-sm hover:shadow-xl transition-all duration-200 space-y-4 ${
                    isLive
                      ? "border-rose-500/40 ring-1 ring-rose-500/20"
                      : "border-card-border hover:border-accent/50"
                  }`}
                >
                  <PushPin color={selectedColor} className="-top-3 left-10" />

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-accent/10 text-accent flex items-center justify-center font-extrabold text-lg border border-accent/20 shrink-0">
                        {session.mentor_name?.charAt(0) || "M"}
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2.5 flex-wrap">
                          <h3 className="font-black text-base text-text">
                            {session.skill_name || "Peer Mentoring Session"}
                          </h3>
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide border flex items-center gap-1 ${
                              isLive
                                ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30 animate-pulse"
                                : session.status === "completed"
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                                : session.status === "cancelled"
                                ? "bg-danger/10 text-danger border-danger/20"
                                : "bg-accent/10 text-accent border-accent/20"
                            }`}
                          >
                            {isLive && <Radio size={10} className="animate-spin" />}
                            <span>{isLive ? "LIVE" : session.status || "Scheduled"}</span>
                          </span>
                        </div>
                        <p className="text-xs text-text-secondary font-medium">
                          Mentor: <strong>{session.mentor_name}</strong> • Learner: <strong>{session.learner_name || "You"}</strong>
                        </p>
                        <p className="text-xs text-text-secondary flex items-center gap-1.5 pt-0.5">
                          <Clock size={13} className="text-accent" />
                          <span>
                            {new Date(session.scheduled_at).toLocaleDateString(undefined, {
                              weekday: "short",
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                            })}{" "}
                            at{" "}
                            {new Date(session.scheduled_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2.5 flex-wrap">
                      {activeTab === "upcoming" && (
                        <>
                          <Link
                            to={`/sessions/${session.id}`}
                            className="px-3.5 py-2 text-xs font-bold rounded-xl bg-surface-elevated hover:bg-bg-alt border border-border text-text transition-colors"
                          >
                            Session Details
                          </Link>

                          {isScheduled && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => startMutation.mutate(session.id)}
                              isLoading={startMutation.isPending}
                              leftIcon={Play}
                              className="text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10 font-bold"
                            >
                              Start
                            </Button>
                          )}

                          {session.meeting_link && (
                            <button
                              type="button"
                              onClick={() => handleJoinCall(session)}
                              className={`px-4 py-2 text-xs font-bold rounded-xl text-white shadow-glow flex items-center gap-1.5 transition-colors cursor-pointer ${
                                isLive
                                  ? "bg-rose-600 hover:bg-rose-700 animate-pulse"
                                  : "bg-accent hover:bg-accent-hover"
                              }`}
                            >
                              <Video size={14} />
                              <span>Join Call</span>
                              <ExternalLink size={12} />
                            </button>
                          )}

                          {isLive && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => completeMutation.mutate(session.id)}
                              isLoading={completeMutation.isPending}
                              leftIcon={CheckCircle}
                              className="text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10 font-bold"
                            >
                              Mark Complete
                            </Button>
                          )}

                          {isScheduled && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => cancelMutation.mutate(session.id)}
                              isLoading={cancelMutation.isPending}
                              leftIcon={XCircle}
                              className="text-danger hover:bg-danger/10 font-bold"
                            >
                              Cancel
                            </Button>
                          )}
                        </>
                      )}

                      {activeTab === "completed" && (
                        <Link
                          to={`/sessions/${session.id}`}
                          className="px-4 py-2 text-xs font-bold rounded-xl bg-surface-elevated hover:bg-bg-alt border border-border text-text transition-colors flex items-center gap-1.5"
                        >
                          <MessageSquare size={14} />
                          <span>View Details & Feedback</span>
                        </Link>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </PageTransition>
  );
}
