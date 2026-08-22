import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import PageTransition from "../components/common/PageTransition";
import { useToast } from "../components/common/Toast";
import {
  ArrowLeft,
  Calendar,
  Clock,
  Video,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertCircle,
  ShieldAlert,
  Sparkles,
  BookOpen,
  User,
  CheckCircle2,
} from "lucide-react";

export default function SessionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  // Fetch session details from authoritative backend
  const {
    data: session,
    isLoading: sessionLoading,
    error: sessionError,
    refetch,
  } = useQuery({
    queryKey: ["sessionDetail", id],
    queryFn: async () => {
      const res = await api.get(`/sessions/${id}`);
      return res.data;
    },
    enabled: !!id,
    retry: false,
  });

  // Complete session mutation
  const completeMutation = useMutation({
    mutationFn: async () => {
      const res = await api.patch(`/sessions/${id}/complete`);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Session marked as COMPLETED! 🎉", "Session Completed");
      queryClient.invalidateQueries({ queryKey: ["sessionDetail", id] });
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
      queryClient.invalidateQueries({ queryKey: ["completedSessions"] });
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["learning-activities"] });
      queryClient.invalidateQueries({ queryKey: ["streak"] });
      queryClient.invalidateQueries({ queryKey: ["heatmap"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to complete session.");
    },
  });

  // Cancel session mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      const res = await api.patch(`/sessions/${id}/cancel`);
      return res.data;
    },
    onSuccess: () => {
      toast.warning("Session has been cancelled and coins refunded.", "Session Cancelled");
      queryClient.invalidateQueries({ queryKey: ["sessionDetail", id] });
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
      queryClient.invalidateQueries({ queryKey: ["cancelledSessions"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to cancel session.");
    },
  });

  if (sessionLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto p-4 text-left">
        <div className="h-8 w-32 bg-border/40 animate-pulse rounded-xl" />
        <div className="h-64 bg-border/40 animate-pulse rounded-3xl" />
      </div>
    );
  }

  const httpStatus = sessionError?.response?.status;

  if (httpStatus === 403) {
    return (
      <div className="max-w-md mx-auto mt-16 text-center">
        <Card className="p-8 space-y-4">
          <div className="p-3.5 bg-danger/10 text-danger rounded-2xl w-fit mx-auto border border-danger/20">
            <ShieldAlert size={36} />
          </div>
          <h2 className="text-xl font-bold text-text">Access Restricted</h2>
          <p className="text-xs text-text-secondary leading-relaxed">
            You are not authorized to view this session. Only confirmed participants (mentor and learner) can access private room details.
          </p>
          <div className="pt-2">
            <Button variant="primary" size="sm" onClick={() => navigate("/sessions")}>
              <ArrowLeft size={14} className="mr-1.5" />
              Back to My Sessions
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (sessionError || !session) {
    return (
      <div className="max-w-md mx-auto mt-16 text-center">
        <Card className="p-8 space-y-4">
          <div className="p-3.5 bg-danger/10 text-danger rounded-2xl w-fit mx-auto border border-danger/20">
            <AlertCircle size={36} />
          </div>
          <h2 className="text-xl font-bold text-text">Session Not Found</h2>
          <p className="text-xs text-text-secondary leading-relaxed">
            The requested mentoring session could not be retrieved or does not exist.
          </p>
          <div className="pt-2">
            <Button variant="primary" size="sm" onClick={() => navigate("/sessions")}>
              <ArrowLeft size={14} className="mr-1.5" />
              Back to Sessions
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const isScheduled = session.status === "scheduled";
  const isCompleted = session.status === "completed";
  const isCancelled = session.status === "cancelled";

  return (
    <PageTransition className="space-y-6 max-w-4xl mx-auto text-left">
      {/* Back Button */}
      <div>
        <button
          type="button"
          onClick={() => navigate("/sessions")}
          className="inline-flex items-center gap-2 text-xs font-bold text-text-secondary hover:text-accent cursor-pointer transition-colors"
        >
          <ArrowLeft size={16} />
          <span>Back to Sessions</span>
        </button>
      </div>

      {/* Main Session Card */}
      <Card
        title={session.skill_name || "1-on-1 Peer Mentoring"}
        subtitle={`Session ID #${session.id}`}
        actions={
          <span
            className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wide border ${
              isCompleted
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                : isCancelled
                ? "bg-danger/10 text-danger border-danger/20"
                : "bg-accent/10 text-accent border-accent/20"
            }`}
          >
            {session.status}
          </span>
        }
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 bg-bg-alt rounded-2xl border border-border/80 space-y-1">
            <p className="text-xs font-bold text-text-secondary flex items-center gap-1.5">
              <User size={13} className="text-accent" /> Mentor
            </p>
            <p className="text-sm font-extrabold text-text">{session.mentor_name}</p>
          </div>

          <div className="p-4 bg-bg-alt rounded-2xl border border-border/80 space-y-1">
            <p className="text-xs font-bold text-text-secondary flex items-center gap-1.5">
              <User size={13} className="text-accent" /> Learner
            </p>
            <p className="text-sm font-extrabold text-text">{session.learner_name}</p>
          </div>

          <div className="p-4 bg-bg-alt rounded-2xl border border-border/80 space-y-1">
            <p className="text-xs font-bold text-text-secondary flex items-center gap-1.5">
              <Calendar size={13} className="text-accent" /> Scheduled Date & Time
            </p>
            <p className="text-sm font-extrabold text-text">
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
            </p>
          </div>

          <div className="p-4 bg-bg-alt rounded-2xl border border-border/80 space-y-1">
            <p className="text-xs font-bold text-text-secondary flex items-center gap-1.5">
              <Clock size={13} className="text-accent" /> Duration
            </p>
            <p className="text-sm font-extrabold text-text">
              {session.duration_minutes || 60} Minutes
            </p>
          </div>
        </div>

        {/* Stable Jitsi Video Room Section */}
        {session.meeting_link && (
          <div className="mt-6 p-5 rounded-2xl bg-accent/5 border border-accent/20 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3.5 text-left">
              <div className="p-3 rounded-xl bg-accent/15 text-accent">
                <Video size={24} />
              </div>
              <div>
                <h4 className="font-extrabold text-sm text-text">Live Jitsi Classroom</h4>
                <p className="text-xs text-text-secondary">
                  Stable meeting room established. Both mentor and learner connect to the same room.
                </p>
              </div>
            </div>

            <a
              href={session.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 text-xs font-extrabold rounded-xl bg-accent text-white hover:bg-accent-hover shadow-glow flex items-center gap-2 transition-all shrink-0"
            >
              <Video size={15} />
              <span>Join Jitsi Call</span>
              <ExternalLink size={13} />
            </a>
          </div>
        )}

        {/* Action Controls */}
        {isScheduled && (
          <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              onClick={() => cancelMutation.mutate()}
              isLoading={cancelMutation.isPending}
              leftIcon={XCircle}
              className="text-danger border-danger/30 hover:bg-danger/10 font-bold text-xs"
            >
              Cancel Session
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => completeMutation.mutate()}
              isLoading={completeMutation.isPending}
              leftIcon={CheckCircle2}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-glow"
            >
              Mark Completed
            </Button>
          </div>
        )}
      </Card>
    </PageTransition>
  );
}
