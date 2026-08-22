import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "motion/react";
import {
  getSessionDetail,
  getSessionParticipants,
  startPeerSession,
  completePeerSession,
  cancelPeerSession,
  joinPeerSession,
  leavePeerSession,
  getSessionPresence,
  submitSessionFeedback,
  getSessionFeedbackList,
} from "../api/sessionApi";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Modal from "../components/common/Modal";
import Avatar from "../components/common/Avatar";
import PageTransition from "../components/common/PageTransition";
import { useToast } from "../components/common/Toast";
import CredibilityBadge from "../components/verification/CredibilityBadge";
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
  Star,
  Play,
  MessageSquare,
  Award,
  Radio,
  Share2,
} from "lucide-react";

export default function SessionDetail() {
  const { id } = useParams();
  const sessionId = parseInt(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [feedbackError, setFeedbackError] = useState("");

  // 1. Fetch Session Detail
  const {
    data: session,
    isLoading: sessionLoading,
    error: sessionError,
  } = useQuery({
    queryKey: ["sessionDetail", sessionId],
    queryFn: () => getSessionDetail(sessionId),
    enabled: !isNaN(sessionId),
    retry: false,
  });

  // 2. Fetch Authoritative Participants Info
  const {
    data: participantsData,
    isLoading: participantsLoading,
  } = useQuery({
    queryKey: ["sessionParticipants", sessionId],
    queryFn: () => getSessionParticipants(sessionId),
    enabled: !isNaN(sessionId) && !!session,
    retry: false,
  });

  // 3. Fetch Session Feedback if Completed
  const {
    data: sessionFeedbacks = [],
    refetch: refetchFeedbacks,
  } = useQuery({
    queryKey: ["sessionFeedbacks", sessionId],
    queryFn: () => getSessionFeedbackList(sessionId),
    enabled: session?.status === "completed",
  });

  // Mutations
  const startMutation = useMutation({
    mutationFn: () => startPeerSession(sessionId),
    onSuccess: () => {
      toast.success("Session is now LIVE! 🚀", "Session Started");
      queryClient.invalidateQueries({ queryKey: ["sessionDetail", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to start session.");
    },
  });

  const completeMutation = useMutation({
    mutationFn: () => completePeerSession(sessionId),
    onSuccess: () => {
      toast.success("Session marked as COMPLETED! 🎉", "Session Completed");
      queryClient.invalidateQueries({ queryKey: ["sessionDetail", sessionId] });
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

  const cancelMutation = useMutation({
    mutationFn: () => cancelPeerSession(sessionId),
    onSuccess: () => {
      setIsCancelModalOpen(false);
      toast.warning("Session has been cancelled and coins refunded.", "Session Cancelled");
      queryClient.invalidateQueries({ queryKey: ["sessionDetail", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
      queryClient.invalidateQueries({ queryKey: ["cancelledSessions"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to cancel session.");
    },
  });

  const feedbackMutation = useMutation({
    mutationFn: (payload) => submitSessionFeedback(payload),
    onSuccess: () => {
      setIsFeedbackModalOpen(false);
      setComment("");
      toast.success("Thank you for submitting feedback! ⭐", "Feedback Recorded");
      refetchFeedbacks();
      queryClient.invalidateQueries({ queryKey: ["mentorProfile"] });
    },
    onError: (err) => {
      setFeedbackError(err.response?.data?.detail || "Failed to submit feedback.");
    },
  });

  const handleJoinCall = async () => {
    try {
      await joinPeerSession(sessionId);
    } catch {
      // Non-blocking presence tracking
    }
    if (session?.meeting_link) {
      window.open(session.meeting_link, "_blank", "noopener,noreferrer");
    }
  };

  const handleFeedbackSubmit = (e) => {
    e.preventDefault();
    setFeedbackError("");

    if (!comment.trim()) {
      setFeedbackError("Please provide a short comment about your session.");
      return;
    }

    const revieweeId =
      participantsData?.current_user_role === "mentor"
        ? participantsData?.learner?.id
        : participantsData?.mentor?.id;

    if (!revieweeId) {
      setFeedbackError("Unable to identify the reviewee.");
      return;
    }

    feedbackMutation.mutate({
      session_id: sessionId,
      reviewee_id: revieweeId,
      rating: parseInt(rating),
      comment: comment.trim(),
    });
  };

  if (sessionLoading || participantsLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto p-4 text-left">
        <div className="h-8 w-32 bg-border/40 animate-pulse rounded-xl" />
        <div className="h-64 bg-border/40 animate-pulse rounded-3xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-44 bg-border/40 animate-pulse rounded-3xl" />
          <div className="h-44 bg-border/40 animate-pulse rounded-3xl" />
        </div>
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
  const isLive = session.status === "in_progress";
  const isCompleted = session.status === "completed";
  const isCancelled = session.status === "cancelled";

  const mentor = participantsData?.mentor;
  const learner = participantsData?.learner;
  const isMentor = participantsData?.current_user_role === "mentor";

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

      {/* Main Session Header Banner */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative p-6 sm:p-8 bg-card-bg border border-card-border rounded-3xl shadow-md overflow-hidden space-y-5"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text">
                {session.skill_name || "1-on-1 Peer Mentoring"}
              </h1>
              <span
                className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wide border flex items-center gap-1.5 ${
                  isLive
                    ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30 animate-pulse"
                    : isCompleted
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                    : isCancelled
                    ? "bg-danger/10 text-danger border-danger/20"
                    : "bg-accent/10 text-accent border-accent/20"
                }`}
              >
                {isLive && <Radio size={12} className="animate-spin" />}
                <span>{isLive ? "LIVE SESSION" : session.status}</span>
              </span>
            </div>
            <p className="text-xs text-text-secondary font-medium">
              Session Workspace #{session.id} • {session.duration_minutes || 60} Minutes
            </p>
          </div>

          {/* Quick Action Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            {isScheduled && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => startMutation.mutate()}
                isLoading={startMutation.isPending}
                leftIcon={Play}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-glow"
              >
                Start Session
              </Button>
            )}

            {isLive && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleJoinCall}
                leftIcon={Video}
                className="bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-glow animate-pulse"
              >
                Join Live Classroom
              </Button>
            )}

            {isCompleted && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsFeedbackModalOpen(true)}
                leftIcon={Star}
                className="bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-glow"
              >
                Leave Feedback
              </Button>
            )}
          </div>
        </div>

        {/* Timing Information Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="p-3.5 bg-bg-alt/90 rounded-2xl border border-border/80 flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-accent/10 text-accent">
              <Calendar size={18} />
            </div>
            <div>
              <p className="text-[11px] font-bold text-text-secondary">Scheduled Date</p>
              <p className="text-xs font-extrabold text-text">
                {new Date(session.scheduled_at).toLocaleDateString(undefined, {
                  weekday: "short",
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                })}
              </p>
            </div>
          </div>

          <div className="p-3.5 bg-bg-alt/90 rounded-2xl border border-border/80 flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-accent/10 text-accent">
              <Clock size={18} />
            </div>
            <div>
              <p className="text-[11px] font-bold text-text-secondary">Time Slot</p>
              <p className="text-xs font-extrabold text-text">
                {new Date(session.scheduled_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </div>

          <div className="p-3.5 bg-bg-alt/90 rounded-2xl border border-border/80 flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-500">
              <CheckCircle size={18} />
            </div>
            <div>
              <p className="text-[11px] font-bold text-text-secondary">Your Role</p>
              <p className="text-xs font-extrabold text-text uppercase">
                {isMentor ? "Mentor (Teaching)" : "Learner (Learning)"}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Participant Relationship Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Mentor Card */}
        <Card
          title={isMentor ? "You (Mentor)" : "Your Mentor"}
          subtitle="Teaching participant"
        >
          <div className="flex items-start gap-4 pt-1">
            <Avatar
              src={mentor?.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${mentor?.name || "Mentor"}`}
              alt={mentor?.name || "Mentor"}
              size="lg"
              className="ring-2 ring-accent/20 shrink-0"
            />
            <div className="space-y-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-extrabold text-base text-text truncate">
                  {mentor?.name || "Mentor"}
                </h3>
                {mentor?.average_rating > 0 && (
                  <span className="flex items-center gap-1 text-xs font-extrabold text-amber-500">
                    <Star size={13} className="fill-amber-500" />
                    <span>{Number(mentor.average_rating).toFixed(1)}</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-text-secondary">
                {mentor?.department ? `${mentor.department} Student` : "Peer Mentor"} • Year {mentor?.year || 1}
              </p>
              {mentor?.bio && (
                <p className="text-xs text-text-secondary line-clamp-2 italic pt-1">
                  "{mentor.bio}"
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Learner Card */}
        <Card
          title={!isMentor ? "You (Learner)" : "Your Student"}
          subtitle="Learning participant"
        >
          <div className="flex items-start gap-4 pt-1">
            <Avatar
              src={learner?.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${learner?.name || "Learner"}`}
              alt={learner?.name || "Learner"}
              size="lg"
              className="ring-2 ring-accent/20 shrink-0"
            />
            <div className="space-y-1 min-w-0">
              <h3 className="font-extrabold text-base text-text truncate">
                {learner?.name || "Learner"}
              </h3>
              <p className="text-xs text-text-secondary">
                {learner?.department ? `${learner.department} Student` : "Peer Learner"} • Year {learner?.year || 1}
              </p>
              {learner?.bio && (
                <p className="text-xs text-text-secondary line-clamp-2 italic pt-1">
                  "{learner.bio}"
                </p>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Jitsi Meeting Room Card */}
      {!isCancelled ? (
        <Card title="Jitsi Video Meeting Room" subtitle="Authoritative secure classroom URL">
          <div className="p-5 rounded-2xl bg-accent/5 border border-accent/20 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3.5 text-left">
              <div className="p-3 rounded-xl bg-accent/15 text-accent">
                <Video size={24} />
              </div>
              <div className="space-y-0.5">
                <h4 className="font-extrabold text-sm text-text">Private Meeting Room</h4>
                <p className="text-xs text-text-secondary font-mono">
                  Room: {session.meeting_room_id || "skillswap-room"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 flex-wrap">
              {(isScheduled || isLive) && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleJoinCall}
                  leftIcon={Video}
                  rightIcon={ExternalLink}
                  className="font-bold text-xs shadow-glow bg-accent hover:bg-accent-hover"
                >
                  Join Jitsi Call
                </Button>
              )}

              {isLive && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => completeMutation.mutate()}
                  isLoading={completeMutation.isPending}
                  leftIcon={CheckCircle2}
                  className="text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10 font-bold text-xs"
                >
                  Mark Completed
                </Button>
              )}

              {isScheduled && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsCancelModalOpen(true)}
                  leftIcon={XCircle}
                  className="text-danger hover:bg-danger/10 font-bold text-xs"
                >
                  Cancel Session
                </Button>
              )}
            </div>
          </div>
        </Card>
      ) : (
        <div className="p-5 rounded-2xl bg-danger/10 border border-danger/20 text-danger text-center space-y-1.5">
          <XCircle size={24} className="mx-auto" />
          <h4 className="font-extrabold text-sm">Session Cancelled</h4>
          <p className="text-xs text-danger/80">
            This session was cancelled. Meeting room access has been closed and coins have been refunded.
          </p>
        </div>
      )}

      {/* Reviews & Feedback Section for Completed Sessions */}
      {isCompleted && (
        <Card
          title="Session Reviews & Outcomes"
          subtitle="Qualitative feedback recorded for this peer exchange"
          actions={
            <Button
              variant="outline"
              size="xs"
              onClick={() => setIsFeedbackModalOpen(true)}
              leftIcon={Star}
              className="text-xs font-bold"
            >
              Add Review
            </Button>
          }
        >
          {sessionFeedbacks.length === 0 ? (
            <div className="p-6 text-center bg-bg-alt rounded-2xl border border-border space-y-2">
              <MessageSquare size={24} className="mx-auto text-text-muted opacity-60" />
              <p className="text-xs font-bold text-text">No feedback submitted yet</p>
              <p className="text-[11px] text-text-secondary max-w-xs mx-auto">
                Share your rating and feedback to help build your peer mentor's credibility.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {sessionFeedbacks.map((fb) => (
                <div
                  key={fb.id}
                  className="p-4 bg-bg-alt rounded-2xl border border-border/80 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1 text-amber-500">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          size={14}
                          className={i < fb.rating ? "fill-amber-500" : "text-border"}
                        />
                      ))}
                      <span className="text-xs font-extrabold text-text ml-1.5">
                        {fb.rating} / 5
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-text-secondary whitespace-pre-line leading-relaxed">
                    "{fb.comment}"
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Cancellation Confirmation Modal */}
      <Modal
        isOpen={isCancelModalOpen}
        onClose={() => !cancelMutation.isPending && setIsCancelModalOpen(false)}
        title="Cancel Mentoring Session"
        size="sm"
      >
        <div className="space-y-4 text-left">
          <p className="text-xs text-text-secondary leading-relaxed">
            Are you sure you want to cancel this session? The slot will be released back to the mentor's availability, and the learner's 5 Skill Coins will be refunded automatically.
          </p>

          <div className="flex justify-end gap-2.5 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCancelModalOpen(false)}
              disabled={cancelMutation.isPending}
              className="text-xs font-semibold"
            >
              Keep Session
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => cancelMutation.mutate()}
              isLoading={cancelMutation.isPending}
              className="bg-danger hover:bg-danger/90 text-white font-bold text-xs"
            >
              Confirm Cancellation
            </Button>
          </div>
        </div>
      </Modal>

      {/* Feedback Submission Modal */}
      <Modal
        isOpen={isFeedbackModalOpen}
        onClose={() => !feedbackMutation.isPending && setIsFeedbackModalOpen(false)}
        title="Leave Session Feedback"
        size="md"
      >
        <form onSubmit={handleFeedbackSubmit} className="space-y-4 text-left">
          {feedbackError && (
            <div className="p-3 text-xs bg-danger/10 border border-danger/20 text-danger rounded-xl font-medium flex items-center gap-2">
              <AlertCircle size={15} className="shrink-0" />
              <span>{feedbackError}</span>
            </div>
          )}

          {/* 1-5 Star Rating Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-text-secondary">
              Rating (1 to 5 Stars)
            </label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className="p-1 text-amber-500 hover:scale-110 transition-transform cursor-pointer"
                >
                  <Star
                    size={24}
                    className={star <= rating ? "fill-amber-500 text-amber-500" : "text-border"}
                  />
                </button>
              ))}
              <span className="text-xs font-extrabold text-text ml-2">
                {rating} / 5 Stars
              </span>
            </div>
          </div>

          {/* Comment Box */}
          <div className="space-y-1.5">
            <label htmlFor="feedback-comment" className="text-xs font-bold text-text-secondary">
              Feedback & Discussion Notes
            </label>
            <textarea
              id="feedback-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="What did you learn? What was helpful during the session? (Max 500 characters)"
              rows={4}
              maxLength={500}
              disabled={feedbackMutation.isPending}
              className="w-full p-3.5 text-xs rounded-xl border border-border bg-bg text-text focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent leading-relaxed"
            />
            <p className="text-[10px] text-text-muted text-right">
              {comment.length} / 500 characters
            </p>
          </div>

          <div className="flex justify-end gap-2.5 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsFeedbackModalOpen(false)}
              disabled={feedbackMutation.isPending}
              className="text-xs font-semibold"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={feedbackMutation.isPending}
              className="font-bold text-xs shadow-glow bg-accent"
            >
              Submit Feedback
            </Button>
          </div>
        </form>
      </Modal>
    </PageTransition>
  );
}
