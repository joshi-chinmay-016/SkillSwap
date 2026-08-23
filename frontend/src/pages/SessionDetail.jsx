import React, { useState, useEffect, useCallback } from "react";
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
  sendSessionHeartbeat,
  getSessionTimeline,
  submitSessionFeedback,
  getSessionFeedbackList,
  saveSessionNotes,
  getSessionNotes,
  addSessionTopic,
  getSessionTopics,
  createSessionActionItem,
  getSessionActionItems,
  updateSessionActionItem,
  deleteSessionActionItem,
  generateSessionIntelligence,
  getSessionIntelligence,
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
  Plus,
  Trash2,
  Tag,
  CheckSquare,
  Square,
  HelpCircle,
  Lightbulb,
  FileText,
  RefreshCw,
  Cpu,
  History,
  Activity,
  Wifi,
  WifiOff,
  Users,
  Timer,
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

  // Workspace View Tab: "collaborative", "timeline", "intelligence"
  const [workspaceTab, setWorkspaceTab] = useState("collaborative");

  // Live notes capture state
  const [activeNotesTab, setActiveNotesTab] = useState("questions");
  const [noteInput, setNoteInput] = useState("");
  const [newTopic, setNewTopic] = useState("");
  const [newActionItem, setNewActionItem] = useState("");
  const [isAutoSaving, setIsAutoSaving] = useState(false);

  // Network connection state
  const [isOnline, setIsOnline] = useState(navigator.onLine);

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

  // 3. Ephemeral Real-Time Presence from Redis
  const { data: presenceData } = useQuery({
    queryKey: ["sessionPresence", sessionId],
    queryFn: () => getSessionPresence(sessionId),
    enabled: !isNaN(sessionId) && !!session && session.status !== "cancelled",
    refetchInterval: 12000, // Ephemeral refresh every 12s
  });

  // 4. Session Timeline Query
  const {
    data: timelineData,
    isLoading: timelineLoading,
    refetch: refetchTimeline,
  } = useQuery({
    queryKey: ["sessionTimeline", sessionId],
    queryFn: () => getSessionTimeline(sessionId),
    enabled: !isNaN(sessionId) && !!session,
  });

  // 5. Fetch Session Feedback if Completed
  const {
    data: sessionFeedbacks = [],
    refetch: refetchFeedbacks,
  } = useQuery({
    queryKey: ["sessionFeedbacks", sessionId],
    queryFn: () => getSessionFeedbackList(sessionId),
    enabled: session?.status === "completed",
  });

  // 6. Phase 4: Fetch Session Notes
  const {
    data: sessionNotes = [],
    refetch: refetchNotes,
  } = useQuery({
    queryKey: ["sessionNotes", sessionId],
    queryFn: () => getSessionNotes(sessionId),
    enabled: !isNaN(sessionId) && !!session,
  });

  // 7. Phase 4: Fetch Session Topics
  const {
    data: sessionTopics = [],
    refetch: refetchTopics,
  } = useQuery({
    queryKey: ["sessionTopics", sessionId],
    queryFn: () => getSessionTopics(sessionId),
    enabled: !isNaN(sessionId) && !!session,
  });

  // 8. Phase 4: Fetch Action Items
  const {
    data: sessionActionItems = [],
    refetch: refetchActionItems,
  } = useQuery({
    queryKey: ["sessionActionItems", sessionId],
    queryFn: () => getSessionActionItems(sessionId),
    enabled: !isNaN(sessionId) && !!session,
  });

  // 9. Phase 4: Fetch Session Intelligence (AI Summary & Post-Session Insights)
  const {
    data: sessionIntelligence,
    isLoading: intelLoading,
    refetch: refetchIntelligence,
  } = useQuery({
    queryKey: ["sessionIntelligence", sessionId],
    queryFn: () => getSessionIntelligence(sessionId),
    enabled: session?.status === "completed",
    retry: false,
  });

  // --- Real-time Presence Heartbeat & Leave Lifecycle ---
  useEffect(() => {
    if (isNaN(sessionId) || !session || session.status === "cancelled") return;

    // Send initial join / heartbeat
    sendSessionHeartbeat(sessionId).catch(() => {});

    // Periodic heartbeat every 20s to refresh TTL
    const heartbeatInterval = setInterval(() => {
      sendSessionHeartbeat(sessionId).catch(() => {});
    }, 20000);

    return () => {
      clearInterval(heartbeatInterval);
      leavePeerSession(sessionId).catch(() => {});
    };
  }, [sessionId, session?.status]);

  // --- Network Reconnection & State Reconciliation ---
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast.success("Network reconnected. Synchronizing session state...", "Online");
      queryClient.invalidateQueries({ queryKey: ["sessionDetail", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionPresence", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionNotes", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionTopics", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionActionItems", sessionId] });
      sendSessionHeartbeat(sessionId).catch(() => {});
    };

    const handleOffline = () => {
      setIsOnline(false);
      toast.warning("Connection interrupted. Reconnecting when network returns...", "Offline ⚠️");
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [sessionId, queryClient, toast]);

  // Determine current user's role
  const isMentor = participantsData?.current_user_role === "mentor";
  const userRole = isMentor ? "mentor" : "learner";

  // Find my saved note
  const myNote = sessionNotes.find((n) => n.role === userRole)?.notes_data || {
    questions: [],
    concepts: [],
    struggles: [],
    takeaways: [],
    resources: [],
    next_steps: [],
  };

  // Mutations
  const startMutation = useMutation({
    mutationFn: () => startPeerSession(sessionId),
    onSuccess: () => {
      toast.success("Session is now LIVE! 🚀", "Session Started");
      queryClient.invalidateQueries({ queryKey: ["sessionDetail", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
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
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionIntelligence", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionPresence", sessionId] });
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
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionPresence", sessionId] });
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
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["mentorProfile"] });
    },
    onError: (err) => {
      setFeedbackError(err.response?.data?.detail || "Failed to submit feedback.");
    },
  });

  // Notes Mutation
  const saveNotesMutation = useMutation({
    mutationFn: (notesData) => saveSessionNotes(sessionId, notesData),
    onSuccess: () => {
      setIsAutoSaving(false);
      refetchNotes();
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
    },
    onError: (err) => {
      setIsAutoSaving(false);
      toast.error(err.response?.data?.detail || "Failed to save note.");
    },
  });

  // Add Topic Mutation
  const addTopicMutation = useMutation({
    mutationFn: (topicName) => addSessionTopic(sessionId, { topic_name: topicName }),
    onSuccess: () => {
      setNewTopic("");
      refetchTopics();
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
      toast.success("Discussion topic tagged!");
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to tag topic.");
    },
  });

  // Action Items Mutations
  const addActionItemMutation = useMutation({
    mutationFn: (title) => createSessionActionItem(sessionId, { title }),
    onSuccess: () => {
      setNewActionItem("");
      refetchActionItems();
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
      toast.success("Action item created!");
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to add action item.");
    },
  });

  const toggleActionItemMutation = useMutation({
    mutationFn: ({ itemId, status }) => updateSessionActionItem(sessionId, itemId, { status }),
    onSuccess: () => {
      refetchActionItems();
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
    },
  });

  const deleteActionItemMutation = useMutation({
    mutationFn: (itemId) => deleteSessionActionItem(sessionId, itemId),
    onSuccess: () => {
      refetchActionItems();
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
      toast.info("Action item deleted.");
    },
  });

  // Generate Intelligence Mutation
  const generateIntelMutation = useMutation({
    mutationFn: () => generateSessionIntelligence(sessionId),
    onSuccess: () => {
      toast.success("Session Intelligence updated! ✨", "Analysis Complete");
      refetchIntelligence();
      refetchActionItems();
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Intelligence generation failed.");
    },
  });

  // Authoritative Jitsi Launcher
  const handleLaunchJitsi = async () => {
    try {
      await joinPeerSession(sessionId);
      queryClient.invalidateQueries({ queryKey: ["sessionPresence", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessionTimeline", sessionId] });
    } catch (e) {
      // Continue opening URL even if ephemeral join had an edge-case error
    }
    window.open(session.meeting_link, "_blank", "noopener,noreferrer");
  };

  const handleAddNoteItem = (e) => {
    e.preventDefault();
    if (!noteInput.trim()) return;

    setIsAutoSaving(true);
    const updatedNotes = {
      ...myNote,
      [activeNotesTab]: [...(myNote[activeNotesTab] || []), noteInput.trim()],
    };

    setNoteInput("");
    saveNotesMutation.mutate(updatedNotes);
  };

  const handleRemoveNoteItem = (tabKey, index) => {
    setIsAutoSaving(true);
    const updatedList = [...(myNote[tabKey] || [])];
    updatedList.splice(index, 1);
    const updatedNotes = {
      ...myNote,
      [tabKey]: updatedList,
    };
    saveNotesMutation.mutate(updatedNotes);
  };

  const handleAddTopic = (e) => {
    e.preventDefault();
    if (!newTopic.trim()) return;
    addTopicMutation.mutate(newTopic.trim());
  };

  const handleAddActionItem = (e) => {
    e.preventDefault();
    if (!newActionItem.trim()) return;
    addActionItemMutation.mutate(newActionItem.trim());
  };

  // Render Status Badge
  const renderStatusBadge = (status) => {
    switch (status) {
      case "in_progress":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-bold rounded-full bg-red-500/10 text-red-500 border border-red-500/20 animate-pulse">
            <Radio className="w-3.5 h-3.5" /> LIVE SESSION
          </span>
        );
      case "completed":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-green-500/10 text-green-500 border border-green-500/20">
            <CheckCircle className="w-3.5 h-3.5" /> Completed
          </span>
        );
      case "cancelled":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-gray-500/10 text-gray-400 border border-gray-500/20">
            <XCircle className="w-3.5 h-3.5" /> Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">
            <Clock className="w-3.5 h-3.5" /> Scheduled
          </span>
        );
    }
  };

  // Render Room Presence Pill in Header
  const renderRoomPresencePill = () => {
    if (session?.status === "cancelled") {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-gray-500/10 text-gray-400 border border-gray-500/20">
          <XCircle className="w-3.5 h-3.5" /> Room Inactive
        </span>
      );
    }

    if (presenceData?.both_present) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          Both in Workspace
        </span>
      );
    }

    if (presenceData?.mentor_present) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
          <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
          Mentor in Room
        </span>
      );
    }

    if (presenceData?.learner_present) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
          Learner in Room
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-surface-hover text-text-muted border border-border">
        <span className="w-2 h-2 rounded-full bg-gray-500"></span>
        Waiting for participants
      </span>
    );
  };

  // Helper for timeline icon
  const getTimelineIcon = (type) => {
    switch (type) {
      case "session_booked":
        return <Calendar className="w-4 h-4 text-primary" />;
      case "session_started":
        return <Play className="w-4 h-4 text-emerald-400" />;
      case "topic_added":
        return <Tag className="w-4 h-4 text-blue-400" />;
      case "note_saved":
        return <FileText className="w-4 h-4 text-amber-400" />;
      case "action_item_created":
        return <CheckSquare className="w-4 h-4 text-purple-400" />;
      case "action_item_completed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case "feedback_submitted":
        return <Star className="w-4 h-4 text-amber-400 fill-current" />;
      case "session_completed":
        return <Award className="w-4 h-4 text-emerald-400" />;
      default:
        return <Activity className="w-4 h-4 text-text-secondary" />;
    }
  };

  if (sessionLoading || participantsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-sm text-text-secondary font-medium">Loading session workspace...</p>
        </div>
      </div>
    );
  }

  if (sessionError) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card className="text-center py-12">
          <ShieldAlert className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-text-primary mb-2">Unauthorized or Not Found</h2>
          <p className="text-text-secondary mb-6 max-w-md mx-auto">
            {sessionError.response?.data?.detail || "You do not have permission to view this peer-learning session."}
          </p>
          <Button onClick={() => navigate("/sessions")}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to My Sessions
          </Button>
        </Card>
      </div>
    );
  }

  const mentor = participantsData?.mentor;
  const learner = participantsData?.learner;
  const skill = participantsData?.skill;
  const isLive = session.status === "in_progress";
  const isCompleted = session.status === "completed";
  const isScheduled = session.status === "scheduled";
  const isCancelled = session.status === "cancelled";

  // Duration label calculation
  const durationLabel = isLive
    ? `~${session.actual_duration_minutes || 1} min (Live)`
    : isCompleted
    ? `${session.actual_duration_minutes || session.duration_minutes || 60} min actual`
    : `${session.duration_minutes || 60} min scheduled`;

  return (
    <PageTransition>
      <div className="max-w-7xl mx-auto space-y-6 pb-12">
        {/* Offline Warning Banner */}
        {!isOnline && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between text-xs text-amber-400 animate-pulse">
            <span className="flex items-center gap-2">
              <WifiOff className="w-4 h-4" />
              Connection interrupted. SkillSwap will automatically reconnect and synchronize state.
            </span>
            <span className="font-mono">Reconnecting...</span>
          </div>
        )}

        {/* Top Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate("/sessions")}
            className="inline-flex items-center text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Sessions
          </button>
          <div className="flex items-center gap-3">
            {renderRoomPresencePill()}
            {renderStatusBadge(session.status)}
            <span className="text-xs text-text-muted font-mono">ID: #{session.id}</span>
          </div>
        </div>

        {/* Hero Banner / Workspace Header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-surface to-surface-hover border border-border/60 p-6 md:p-8 shadow-sm">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-md text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                  {skill?.name || "Peer Mentoring"}
                </span>
                <span className="flex items-center gap-1 text-xs text-text-muted font-medium bg-surface/60 px-2.5 py-1 rounded-md border border-border/50">
                  <Timer className="w-3.5 h-3.5 text-primary" /> {durationLabel}
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold text-text-primary">
                Peer Learning: {skill?.name || "Mentoring Session"}
              </h1>
              <div className="flex flex-wrap items-center gap-4 text-sm text-text-secondary">
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-primary" />
                  {new Date(session.scheduled_at).toLocaleDateString(undefined, {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-primary" />
                  {new Date(session.scheduled_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </div>

            {/* Lifecycle Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              {isScheduled && isMentor && (
                <Button
                  onClick={() => startMutation.mutate()}
                  loading={startMutation.isPending}
                  className="bg-green-600 hover:bg-green-500 text-white font-semibold shadow-lg shadow-green-600/20"
                >
                  <Play className="w-4 h-4 mr-2" /> Start Live Session
                </Button>
              )}

              {isLive && (
                <Button
                  onClick={handleLaunchJitsi}
                  className="bg-primary text-white hover:bg-primary-hover font-bold shadow-lg shadow-primary/25"
                >
                  <Video className="w-4 h-4 mr-2" /> Join Authoritative Jitsi Room
                  <ExternalLink className="w-3.5 h-3.5 ml-1.5 opacity-70" />
                </Button>
              )}

              {(isLive || isScheduled) && (
                <Button
                  onClick={() => completeMutation.mutate()}
                  loading={completeMutation.isPending}
                  variant="outline"
                  className="border-green-500/30 text-green-500 hover:bg-green-500/10 font-medium"
                >
                  <CheckCircle2 className="w-4 h-4 mr-1.5" /> Mark Completed
                </Button>
              )}

              {(isScheduled || isLive) && (
                <Button
                  onClick={() => setIsCancelModalOpen(true)}
                  variant="outline"
                  className="border-red-500/30 text-red-500 hover:bg-red-500/10 font-medium"
                >
                  Cancel Session
                </Button>
              )}

              {isCompleted && (
                <Button
                  onClick={() => setIsFeedbackModalOpen(true)}
                  className="bg-amber-500 hover:bg-amber-400 text-black font-semibold shadow-lg shadow-amber-500/20"
                >
                  <Star className="w-4 h-4 mr-1.5 fill-current" /> Leave Feedback
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* View Switcher Tabs (Collaborative Workspace / Timeline / Intelligence) */}
        <div className="flex border-b border-border/60 gap-4">
          <button
            onClick={() => setWorkspaceTab("collaborative")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              workspaceTab === "collaborative"
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            <BookOpen className="w-4 h-4" /> Collaborative Learning
          </button>
          <button
            onClick={() => setWorkspaceTab("timeline")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              workspaceTab === "timeline"
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            <History className="w-4 h-4" /> Session Timeline
            {timelineData?.events?.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-surface-hover text-text-secondary border border-border">
                {timelineData.events.length}
              </span>
            )}
          </button>
          {isCompleted && (
            <button
              onClick={() => setWorkspaceTab("intelligence")}
              className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
                workspaceTab === "intelligence"
                  ? "border-primary text-primary"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              <Sparkles className="w-4 h-4 text-amber-400" /> AI Intelligence Report
            </button>
          )}
        </div>

        {/* 2-Column Workspace Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column (2 Cols on lg) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Cancelled Banner if session is cancelled */}
            {isCancelled && (
              <Card className="p-6 border-red-500/20 bg-red-500/5 text-center space-y-2">
                <XCircle className="w-10 h-10 text-red-500 mx-auto" />
                <h3 className="text-base font-bold text-text-primary">This session has been cancelled</h3>
                <p className="text-xs text-text-secondary max-w-md mx-auto">
                  This meeting is no longer active. Coins have been returned to the learner wallet and mentor calendar slots released.
                </p>
              </Card>
            )}

            {/* Live Video Call Frame when Live */}
            {isLive && (
              <Card className="p-6 border-red-500/20 bg-gradient-to-b from-red-500/5 to-transparent">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                    </span>
                    <h3 className="font-bold text-text-primary">Live Jitsi Meeting Room</h3>
                  </div>
                  <span className="text-xs text-text-muted font-mono">Room: {session.meeting_room_id}</span>
                </div>
                <div className="rounded-xl overflow-hidden bg-black/80 aspect-video flex flex-col items-center justify-center text-center p-6 border border-border/40">
                  <Video className="w-12 h-12 text-primary mb-3 animate-pulse" />
                  <h4 className="text-lg font-semibold text-white mb-2">Authoritative Video Meeting</h4>
                  <p className="text-sm text-gray-300 max-w-md mb-6">
                    Connect directly with your peer in the secure Jitsi meeting room. Use the collaborative notes and action item panel below to capture learning in real time.
                  </p>
                  <Button
                    onClick={handleLaunchJitsi}
                    size="lg"
                    className="bg-primary text-white hover:bg-primary-hover font-bold shadow-xl shadow-primary/30 transform hover:-translate-y-0.5"
                  >
                    <Video className="w-5 h-5 mr-2" /> Launch Jitsi Meeting
                    <ExternalLink className="w-4 h-4 ml-2 opacity-75" />
                  </Button>
                </div>
              </Card>
            )}

            {/* --- TAB 1: COLLABORATIVE LEARNING --- */}
            {workspaceTab === "collaborative" && (
              <div className="space-y-6">
                {/* Notes Capture Panel */}
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4 pb-3 border-b border-border/60">
                    <div className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-primary" />
                      <h3 className="font-bold text-text-primary">
                        {isMentor ? "Mentor Teaching Notes" : "Learner Notes & Questions"}
                      </h3>
                    </div>
                    <span className="text-xs text-text-muted flex items-center gap-1">
                      {isAutoSaving ? (
                        <span className="text-amber-400 animate-pulse">Saving...</span>
                      ) : (
                        <span className="text-emerald-400">✓ Synchronized in real-time</span>
                      )}
                    </span>
                  </div>

                  {/* Note Category Tabs */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {(isMentor
                      ? [
                          { key: "concepts", label: "Concepts Taught" },
                          { key: "resources", label: "Resources Shared" },
                          { key: "struggles", label: "Struggles Observed" },
                          { key: "next_steps", label: "Recommended Practice" },
                        ]
                      : [
                          { key: "questions", label: "Questions Asked" },
                          { key: "concepts", label: "Concepts Learned" },
                          { key: "struggles", label: "Difficult Topics" },
                          { key: "takeaways", label: "Key Takeaways" },
                        ]
                    ).map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setActiveNotesTab(tab.key)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          activeNotesTab === tab.key
                            ? "bg-primary text-white shadow-sm"
                            : "bg-surface-hover text-text-secondary hover:text-text-primary"
                        }`}
                      >
                        {tab.label} ({(myNote[tab.key] || []).length})
                      </button>
                    ))}
                  </div>

                  {/* Note Items List */}
                  <div className="space-y-2 mb-4 min-h-[100px] max-h-[220px] overflow-y-auto">
                    {(myNote[activeNotesTab] || []).length === 0 ? (
                      <div className="py-6 text-center text-xs text-text-muted">
                        Capture your first learning note or question under this category.
                      </div>
                    ) : (
                      (myNote[activeNotesTab] || []).map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-2.5 rounded-lg bg-surface-hover/70 border border-border/50 text-xs text-text-primary group"
                        >
                          <span>{item}</span>
                          <button
                            onClick={() => handleRemoveNoteItem(activeNotesTab, index)}
                            className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity p-1"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  {/* Add Note Input */}
                  <form onSubmit={handleAddNoteItem} className="flex gap-2">
                    <input
                      type="text"
                      value={noteInput}
                      onChange={(e) => setNoteInput(e.target.value)}
                      placeholder={`Add a note under ${activeNotesTab}...`}
                      className="flex-1 px-3 py-2 text-xs rounded-lg bg-surface-hover border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
                    />
                    <Button type="submit" size="sm" className="text-xs">
                      <Plus className="w-3.5 h-3.5 mr-1" /> Add Note
                    </Button>
                  </form>
                </Card>

                {/* Action Items & Next Steps Tracker */}
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4 pb-3 border-b border-border/60">
                    <div className="flex items-center gap-2">
                      <CheckSquare className="w-5 h-5 text-emerald-500" />
                      <h3 className="font-bold text-text-primary">Action Items & Next Steps</h3>
                    </div>
                    <span className="text-xs text-text-muted">
                      {sessionActionItems.filter((a) => a.status === "completed").length} / {sessionActionItems.length} completed
                    </span>
                  </div>

                  {/* Action Items List */}
                  <div className="space-y-2 mb-4">
                    {sessionActionItems.length === 0 ? (
                      <p className="text-xs text-text-muted py-4 text-center">
                        No action items created yet. Add practical tasks or homework to reinforce learning.
                      </p>
                    ) : (
                      sessionActionItems.map((item) => {
                        const isDone = item.status === "completed";
                        return (
                          <div
                            key={item.id}
                            className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                              isDone
                                ? "bg-green-500/5 border-green-500/20 text-text-muted"
                                : "bg-surface-hover/70 border-border text-text-primary"
                            }`}
                          >
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <button
                                onClick={() =>
                                  toggleActionItemMutation.mutate({
                                    itemId: item.id,
                                    status: isDone ? "pending" : "completed",
                                  })
                                }
                                className="text-text-muted hover:text-primary transition-colors flex-shrink-0"
                              >
                                {isDone ? (
                                  <CheckCircle2 className="w-4 h-4 text-green-500 fill-green-500/20" />
                                ) : (
                                  <Square className="w-4 h-4" />
                                )}
                              </button>
                              <div className="min-w-0">
                                <p className={`text-xs font-medium ${isDone ? "line-through text-text-muted" : ""}`}>
                                  {item.title}
                                </p>
                                {item.description && (
                                  <p className="text-[11px] text-text-muted truncate">{item.description}</p>
                                )}
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              {item.source === "ai_extracted" && (
                                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/10 text-primary">
                                  AI
                                </span>
                              )}
                              <button
                                onClick={() => deleteActionItemMutation.mutate(item.id)}
                                className="text-text-muted hover:text-red-400 transition-colors p-1"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  {/* Add Action Item Form */}
                  <form onSubmit={handleAddActionItem} className="flex gap-2">
                    <input
                      type="text"
                      value={newActionItem}
                      onChange={(e) => setNewActionItem(e.target.value)}
                      placeholder="e.g. Complete Redis caching exercises..."
                      className="flex-1 px-3 py-2 text-xs rounded-lg bg-surface-hover border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
                    />
                    <Button type="submit" size="sm" className="text-xs">
                      <Plus className="w-3.5 h-3.5 mr-1" /> Add Task
                    </Button>
                  </form>
                </Card>
              </div>
            )}

            {/* --- TAB 2: SESSION TIMELINE (AUTHORITATIVE FROM DB) --- */}
            {workspaceTab === "timeline" && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-border/60">
                  <div className="flex items-center gap-2.5">
                    <History className="w-5 h-5 text-primary" />
                    <div>
                      <h3 className="text-base font-bold text-text-primary">Authoritative Session Timeline</h3>
                      <p className="text-xs text-text-muted">
                        Chronological record of verified session milestones and peer collaboration.
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={() => refetchTimeline()}
                    variant="outline"
                    size="sm"
                    className="text-xs"
                  >
                    <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
                  </Button>
                </div>

                {timelineLoading ? (
                  <div className="py-8 text-center text-xs text-text-muted">
                    <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    Loading timeline milestones...
                  </div>
                ) : !timelineData?.events || timelineData.events.length === 0 ? (
                  <div className="py-12 text-center text-text-muted space-y-2">
                    <History className="w-10 h-10 mx-auto text-text-muted/40" />
                    <p className="text-xs">No discussion topics or notes captured yet.</p>
                  </div>
                ) : (
                  <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border/70">
                    {timelineData.events.map((ev, idx) => (
                      <div key={ev.id || idx} className="relative group">
                        {/* Milestone Node */}
                        <div className="absolute -left-[27px] top-0.5 w-6 h-6 rounded-full bg-surface border-2 border-primary/60 flex items-center justify-center shadow-sm">
                          {getTimelineIcon(ev.type)}
                        </div>

                        {/* Event Content */}
                        <div className="bg-surface-hover/50 p-3.5 rounded-xl border border-border/60 hover:border-primary/40 transition-all space-y-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold text-text-primary">{ev.title}</span>
                            <span className="text-[11px] font-mono text-text-muted">
                              {new Date(ev.timestamp).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                          {ev.description && (
                            <p className="text-xs text-text-secondary leading-relaxed">{ev.description}</p>
                          )}
                          {ev.actor_role && (
                            <div className="pt-1">
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-surface border border-border text-text-muted uppercase tracking-wider">
                                {ev.actor_role}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}

            {/* --- TAB 3: PHASE 4 POST-SESSION INTELLIGENCE --- */}
            {workspaceTab === "intelligence" && isCompleted && (
              <div className="space-y-6">
                <Card className="p-6 border-primary/20 bg-gradient-to-br from-primary/5 via-surface to-surface">
                  <div className="flex items-center justify-between mb-6 pb-4 border-b border-border/60">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                        <Sparkles className="w-5 h-5 text-amber-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-text-primary">AI Session Intelligence</h3>
                        <p className="text-xs text-text-muted">
                          {sessionIntelligence?.provenance?.provider
                            ? `Grounded analysis • ${sessionIntelligence.provenance.provider}`
                            : "Grounded in participant notes & discussion topics"}
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => generateIntelMutation.mutate()}
                      loading={generateIntelMutation.isPending}
                      variant="outline"
                      size="sm"
                      className="text-xs"
                    >
                      <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Refresh Analysis
                    </Button>
                  </div>

                  {sessionIntelligence?.status === "insufficient_data" ? (
                    <div className="p-5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-center space-y-2">
                      <AlertCircle className="w-8 h-8 text-amber-500 mx-auto" />
                      <h4 className="font-semibold text-amber-400 text-sm">Notice: Insufficient Session Signals</h4>
                      <p className="text-xs text-text-secondary max-w-md mx-auto">
                        This session did not have enough captured notes or discussion topics to generate a reliable AI summary. SkillSwap does not fabricate transcripts.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* AI Executive Summary */}
                      <div className="p-4 rounded-xl bg-surface-hover/60 border border-border/50">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-primary mb-2 flex items-center gap-1.5">
                          <Cpu className="w-3.5 h-3.5" /> Executive Summary
                        </h4>
                        <p className="text-sm text-text-primary leading-relaxed">
                          {sessionIntelligence?.summary || "Session completed successfully."}
                        </p>
                      </div>

                      {/* Topics Covered */}
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary flex items-center gap-1.5">
                          <Tag className="w-3.5 h-3.5" /> Topics & Skills Covered
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {(sessionIntelligence?.topics_covered || []).map((t, idx) => (
                            <span
                              key={idx}
                              className="px-3 py-1 rounded-lg text-xs font-medium bg-surface-hover text-text-primary border border-border"
                            >
                              {typeof t === "string" ? t : t.name || skill?.name}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* 2-Column Takeaways: Learner vs Mentor */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 rounded-xl bg-surface-hover/40 border border-border/40 space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
                            <BookOpen className="w-3.5 h-3.5" /> Learner Insights
                          </h4>
                          <p className="text-xs text-text-secondary leading-relaxed">
                            {sessionIntelligence?.learner_notes_summary ||
                              (sessionIntelligence?.key_takeaways?.length
                                ? sessionIntelligence.key_takeaways.join("; ")
                                : "Learner reviewed foundational concepts with mentor.")}
                          </p>
                        </div>

                        <div className="p-4 rounded-xl bg-surface-hover/40 border border-border/40 space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                            <Award className="w-3.5 h-3.5" /> Mentor Guidance
                          </h4>
                          <p className="text-xs text-text-secondary leading-relaxed">
                            {sessionIntelligence?.mentor_notes_summary ||
                              "Mentor provided architectural guidance and recommended practice exercises."}
                          </p>
                        </div>
                      </div>

                      {/* Recommended Next Steps */}
                      {sessionIntelligence?.recommended_next_steps?.length > 0 && (
                        <div className="p-4 rounded-xl bg-primary/5 border border-primary/15 space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                            <Lightbulb className="w-3.5 h-3.5" /> Recommended Next Steps
                          </h4>
                          <ul className="space-y-1.5">
                            {sessionIntelligence.recommended_next_steps.map((step, idx) => (
                              <li key={idx} className="text-xs text-text-secondary flex items-start gap-2">
                                <span className="text-primary font-bold">•</span>
                                <span>{step}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              </div>
            )}
          </div>

          {/* Right Column: Participant Profiles & Live Topics */}
          <div className="space-y-6">
            {/* Live Discussion Topics Card */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-border/60">
                <div className="flex items-center gap-2">
                  <Tag className="w-5 h-5 text-primary" />
                  <h3 className="font-bold text-text-primary">Discussion Topics</h3>
                </div>
                <span className="text-xs text-text-muted">{sessionTopics.length} tags</span>
              </div>

              {/* Topic Pills */}
              <div className="flex flex-wrap gap-2 mb-4 min-h-[48px]">
                {sessionTopics.length === 0 ? (
                  <p className="text-xs text-text-muted py-2">Tag discussion topics covered during your session.</p>
                ) : (
                  sessionTopics.map((top) => (
                    <span
                      key={top.id}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20"
                    >
                      #{top.topic_name}
                    </span>
                  ))
                )}
              </div>

              {/* Add Topic Form */}
              <form onSubmit={handleAddTopic} className="flex gap-2">
                <input
                  type="text"
                  value={newTopic}
                  onChange={(e) => setNewTopic(e.target.value)}
                  placeholder="Tag topic (e.g. WebSocket)..."
                  className="flex-1 px-3 py-1.5 text-xs rounded-lg bg-surface-hover border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
                />
                <Button type="submit" size="sm" className="text-xs">
                  Tag
                </Button>
              </form>
            </Card>

            {/* Mentor Card */}
            <Card className="p-6">
              <div className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-4 flex items-center justify-between">
                <span>Peer Mentor</span>
                <div className="flex items-center gap-2">
                  {presenceData?.mentor_present ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Online
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] text-text-muted bg-surface-hover px-2 py-0.5 rounded-full border border-border">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-500"></span> Offline
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400">
                    TEACHER
                  </span>
                </div>
              </div>

              <div className="flex items-start gap-3.5 mb-4">
                <Avatar
                  src={mentor?.avatar_url}
                  name={mentor?.name || "Mentor"}
                  size="lg"
                  className="border-2 border-primary/30"
                />
                <div className="min-w-0 flex-1">
                  <h4 className="font-bold text-text-primary text-base truncate">
                    {mentor?.name || "Mentor"}
                  </h4>
                  <p className="text-xs text-text-muted truncate">
                    {mentor?.department ? `${mentor.department} • Year ${mentor.year || 1}` : "Peer Mentor"}
                  </p>
                  {mentor?.average_rating > 0 && (
                    <div className="flex items-center gap-1 mt-1 text-xs text-amber-400 font-semibold">
                      <Star className="w-3.5 h-3.5 fill-current" />
                      <span>{mentor.average_rating.toFixed(1)} / 5.0</span>
                    </div>
                  )}
                </div>
              </div>
              {mentor?.bio && (
                <p className="text-xs text-text-secondary line-clamp-3 bg-surface-hover/50 p-3 rounded-lg border border-border/40">
                  "{mentor.bio}"
                </p>
              )}
            </Card>

            {/* Learner Card */}
            <Card className="p-6">
              <div className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-4 flex items-center justify-between">
                <span>Peer Learner</span>
                <div className="flex items-center gap-2">
                  {presenceData?.learner_present ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Online
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] text-text-muted bg-surface-hover px-2 py-0.5 rounded-full border border-border">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-500"></span> Offline
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400">
                    STUDENT
                  </span>
                </div>
              </div>

              <div className="flex items-start gap-3.5">
                <Avatar
                  src={learner?.avatar_url}
                  name={learner?.name || "Learner"}
                  size="lg"
                  className="border-2 border-blue-500/30"
                />
                <div className="min-w-0 flex-1">
                  <h4 className="font-bold text-text-primary text-base truncate">
                    {learner?.name || "Learner"}
                  </h4>
                  <p className="text-xs text-text-muted truncate">
                    {learner?.department ? `${learner.department} • Year ${learner.year || 1}` : "Peer Student"}
                  </p>
                </div>
              </div>
            </Card>

            {/* Existing Feedback Display */}
            {sessionFeedbacks.length > 0 && (
              <Card className="p-6">
                <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-3 flex items-center gap-1.5">
                  <Star className="w-4 h-4 text-amber-400 fill-current" /> Session Reviews ({sessionFeedbacks.length})
                </h4>
                <div className="space-y-3">
                  {sessionFeedbacks.map((fb) => (
                    <div key={fb.id} className="p-3 rounded-lg bg-surface-hover/60 border border-border/40 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-text-primary">
                          {fb.reviewer?.name || "Peer"}
                        </span>
                        <div className="flex items-center text-amber-400 text-xs">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <Star
                              key={i}
                              className={`w-3 h-3 ${i < fb.rating ? "fill-current" : "text-gray-600"}`}
                            />
                          ))}
                        </div>
                      </div>
                      {fb.comment && <p className="text-xs text-text-secondary italic">"{fb.comment}"</p>}
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>

        {/* Feedback Modal */}
        <Modal
          isOpen={isFeedbackModalOpen}
          onClose={() => setIsFeedbackModalOpen(false)}
          title="Rate Your Peer Learning Session"
        >
          <div className="space-y-5">
            <p className="text-sm text-text-secondary">
              How was your session with {isMentor ? learner?.name : mentor?.name}? Your feedback builds community trust.
            </p>

            {feedbackError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {feedbackError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-2 uppercase">
                Rating (1 - 5 Stars)
              </label>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className="p-1.5 transition-transform hover:scale-110 focus:outline-none"
                  >
                    <Star
                      className={`w-8 h-8 ${
                        star <= rating ? "text-amber-400 fill-current" : "text-gray-600 hover:text-amber-300"
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-2 uppercase">
                Comments & Observations
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="What did you learn? How helpful was your peer partner?"
                rows={4}
                className="w-full px-3.5 py-2.5 rounded-xl bg-surface-hover border border-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary resize-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={() => setIsFeedbackModalOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() =>
                  feedbackMutation.mutate({
                    session_id: parseInt(sessionId, 10),
                    reviewee_id: isMentor ? session?.requester_id : session?.mentor_id,
                    rating: parseInt(rating, 10),
                    comment: comment.trim(),
                  })
                }
                loading={feedbackMutation.isPending}
                className="bg-amber-500 hover:bg-amber-400 text-black font-semibold"
              >
                Submit Feedback
              </Button>
            </div>
          </div>
        </Modal>

        {/* Cancel Confirmation Modal */}
        <Modal
          isOpen={isCancelModalOpen}
          onClose={() => setIsCancelModalOpen(false)}
          title="Cancel Peer Session?"
        >
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">
              Are you sure you want to cancel this booking? If you are the learner, your 5 coins will be refunded immediately and the mentor's calendar slot will be released.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={() => setIsCancelModalOpen(false)}>
                Keep Session
              </Button>
              <Button
                variant="danger"
                onClick={() => cancelMutation.mutate()}
                loading={cancelMutation.isPending}
              >
                Confirm Cancellation
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </PageTransition>
  );
}
