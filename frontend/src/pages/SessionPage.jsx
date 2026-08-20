import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLearningSession, useCompleteSession, useArchiveSession } from "../hooks/useSessions";
import SessionStatusBadge from "../components/JourneySessions/SessionStatusBadge";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Skeleton from "../components/common/Skeleton";
import SectionHeader from "../components/common/SectionHeader";
import PageTransition from "../components/common/PageTransition";
import { useToast } from "../components/common/Toast";
import {
  ArrowLeft,
  Sparkles,
  Clock,
  Calendar,
  CheckCircle2,
  Archive,
  Brain,
  MessageSquare,
  Bot,
  Layers,
  AlertCircle,
  FileText,
  Video,
  ExternalLink,
} from "lucide-react";

export default function SessionPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [sessionNotes, setSessionNotes] = useState("");

  const { data: session, isLoading, error } = useLearningSession(sessionId);
  const completeSessionMutation = useCompleteSession(session?.journey_id);
  const archiveSessionMutation = useArchiveSession(session?.journey_id);

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto p-4">
        <Skeleton variant="rectangular" width="120px" height="32px" />
        <Skeleton variant="text" width="60%" height="32px" />
        <Card className="p-6 space-y-4">
          <Skeleton variant="text" width="40%" height="20px" />
          <Skeleton variant="text" width="80%" height="16px" />
        </Card>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="max-w-md mx-auto mt-12">
        <Card className="text-center py-8 px-6">
          <div className="p-3 bg-danger/10 text-danger rounded-full w-fit mx-auto mb-4">
            <AlertCircle size={32} />
          </div>
          <h2 className="text-lg font-bold text-text">Session Not Found</h2>
          <p className="text-sm text-text-secondary mt-2">
            The requested learning session could not be retrieved or does not exist.
          </p>
          <div className="mt-6">
            <Button variant="primary" size="sm" onClick={() => navigate(-1)}>
              <ArrowLeft size={14} className="mr-1.5" />
              Go Back
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const handleComplete = () => {
    completeSessionMutation.mutate(session.id, {
      onSuccess: () => {
        toast.show("Session marked as COMPLETED! 🎉", "success");
      },
      onError: (err) => {
        toast.show(err.response?.data?.detail || "Failed to complete session", "error");
      },
    });
  };

  const handleArchive = () => {
    archiveSessionMutation.mutate(session.id, {
      onSuccess: () => {
        toast.show("Session ARCHIVED.", "info");
      },
      onError: (err) => {
        toast.show(err.response?.data?.detail || "Failed to archive session", "error");
      },
    });
  };

  const status = (session.status || "").toUpperCase();

  return (
    <PageTransition className="space-y-6 max-w-4xl mx-auto text-left">
      {/* Top Header Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <button
            onClick={() => navigate(session.journey_id ? `/journey/${session.journey_id}` : "/sessions")}
            className="flex items-center text-xs font-semibold text-text-secondary hover:text-accent w-fit transition-colors gap-1 group cursor-pointer"
          >
            <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
            <span>{session.journey_id ? "Back to Learning Journey" : "Back to Sessions"}</span>
          </button>

          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text">
              {session.title || "Live Learning Session"}
            </h1>
            <SessionStatusBadge status={status} />
          </div>

          <p className="text-xs text-text-muted font-mono">
            Session ID: {session.uuid || session.id}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {status === "ACTIVE" && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleArchive}
                disabled={archiveSessionMutation.isPending}
                leftIcon={Archive}
                className="text-text-secondary hover:text-danger hover:border-danger/30"
              >
                Archive
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleComplete}
                disabled={completeSessionMutation.isPending}
                leftIcon={CheckCircle2}
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-glow"
              >
                Complete Session
              </Button>
            </>
          )}

          {status === "COMPLETED" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleArchive}
              disabled={archiveSessionMutation.isPending}
              leftIcon={Archive}
              className="text-text-secondary hover:text-danger hover:border-danger/30"
            >
              Archive
            </Button>
          )}
        </div>
      </div>

      {/* Main Details Grid */}
      <Card title="Session Metadata & Timing">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs pt-2">
          <div className="p-3.5 bg-bg-alt rounded-xl border border-border/70">
            <span className="text-text-secondary font-medium block">Started At</span>
            <span className="text-text font-bold mt-1 flex items-center gap-1.5 text-sm">
              <Clock size={15} className="text-accent" />
              {session.started_at ? new Date(session.started_at).toLocaleString() : "Pending Start"}
            </span>
          </div>

          <div className="p-3.5 bg-bg-alt rounded-xl border border-border/70">
            <span className="text-text-secondary font-medium block">Ended At</span>
            <span className="text-text font-bold mt-1 flex items-center gap-1.5 text-sm">
              <CheckCircle2 size={15} className="text-emerald-500" />
              {session.ended_at ? new Date(session.ended_at).toLocaleString() : "In Progress"}
            </span>
          </div>

          <div className="p-3.5 bg-bg-alt rounded-xl border border-border/70">
            <span className="text-text-secondary font-medium block">Created Date</span>
            <span className="text-text font-bold mt-1 flex items-center gap-1.5 text-sm">
              <Calendar size={15} className="text-accent" />
              {new Date(session.created_at || Date.now()).toLocaleDateString()}
            </span>
          </div>
        </div>
      </Card>

      {/* Live Notes Area */}
      <Card title="Session Notes & Key Learnings" subtitle="Capture important discussion points and code snippets">
        <div className="space-y-3">
          <textarea
            value={sessionNotes}
            onChange={(e) => setSessionNotes(e.target.value)}
            placeholder="Write key concepts, debugging tips, and next steps discussed in this session..."
            rows={4}
            className="w-full p-3.5 text-xs rounded-xl border border-border bg-bg text-text focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent leading-relaxed"
          />
          <div className="flex justify-end">
            <Button
              size="xs"
              variant="secondary"
              onClick={() => toast.show("Session notes saved locally.", "success")}
            >
              Save Notes
            </Button>
          </div>
        </div>
      </Card>

      {/* AI Assistant Ready Container */}
      <Card className="p-8 border-accent/25 bg-gradient-to-br from-accent/5 via-surface-elevated to-bg relative overflow-hidden shadow-md">
        <div className="max-w-md mx-auto text-center space-y-4">
          <div className="p-3.5 bg-accent/15 text-accent rounded-2xl w-fit mx-auto shadow-xs">
            <Bot size={32} />
          </div>

          <div className="space-y-1.5">
            <h3 className="text-lg font-bold text-text">
              Context-Aware AI Mentor Linked
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              This session is established as a persistent anchor for your learning journey. You can analyze discussion takeaways with the AI Mentor anytime.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-[11px]">
            <span className="px-3 py-1 bg-bg border border-border rounded-full text-text-secondary font-semibold flex items-center gap-1">
              <MessageSquare size={12} className="text-accent" /> Session Chat
            </span>
            <span className="px-3 py-1 bg-bg border border-border rounded-full text-text-secondary font-semibold flex items-center gap-1">
              <Sparkles size={12} className="text-emerald-500" /> AI Grounding
            </span>
            <span className="px-3 py-1 bg-bg border border-border rounded-full text-text-secondary font-semibold flex items-center gap-1">
              <Brain size={12} className="text-amber-500" /> Mentor Memory
            </span>
          </div>
        </div>
      </Card>
    </PageTransition>
  );
}
