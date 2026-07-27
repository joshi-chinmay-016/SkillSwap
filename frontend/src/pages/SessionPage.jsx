import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLearningSession, useCompleteSession, useArchiveSession } from "../hooks/useSessions";
import SessionStatusBadge from "../components/JourneySessions/SessionStatusBadge";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Skeleton from "../components/common/Skeleton";
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
  AlertCircle
} from "lucide-react";

/**
 * SessionPage Component
 * Displays metadata for a single Learning Session and prepares the space for future AI Mentor & Chat features.
 */
export default function SessionPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const { data: session, isLoading, error } = useLearningSession(sessionId);
  const completeSessionMutation = useCompleteSession(session?.journey_id);
  const archiveSessionMutation = useArchiveSession(session?.journey_id);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 max-w-4xl mx-auto p-4">
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
    <div className="flex flex-col gap-6 max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <button
            onClick={() => navigate(`/journey/${session.journey_id}`)}
            className="flex items-center text-xs font-semibold text-text-secondary hover:text-accent w-fit transition-colors gap-1 group"
          >
            <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
            Back to Journey
          </button>
          
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-text">
              {session.title}
            </h1>
            <SessionStatusBadge status={status} />
          </div>
          
          <p className="text-xs text-text-secondary font-mono">
            Session ID: {session.uuid}
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex items-center gap-2">
          {status === "ACTIVE" && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleArchive}
                disabled={archiveSessionMutation.isPending}
                className="text-text-secondary hover:text-danger hover:border-danger/30"
              >
                <Archive size={14} className="mr-1.5" />
                Archive
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleComplete}
                disabled={completeSessionMutation.isPending}
                className="bg-success hover:bg-success/90 text-white border-none"
              >
                <CheckCircle2 size={14} className="mr-1.5" />
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
              className="text-text-secondary hover:text-danger hover:border-danger/30"
            >
              <Archive size={14} className="mr-1.5" />
              Archive
            </Button>
          )}
        </div>
      </div>

      {/* Main Details Card */}
      <Card title="Session Overview">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs pt-2">
          <div className="p-3 bg-bg-alt rounded-lg border border-border/60">
            <span className="text-text-secondary font-medium block">Started At</span>
            <span className="text-text font-bold mt-1 flex items-center gap-1.5 text-sm">
              <Clock size={14} className="text-accent" />
              {new Date(session.started_at).toLocaleString()}
            </span>
          </div>

          <div className="p-3 bg-bg-alt rounded-lg border border-border/60">
            <span className="text-text-secondary font-medium block">Ended At</span>
            <span className="text-text font-bold mt-1 flex items-center gap-1.5 text-sm">
              <CheckCircle2 size={14} className="text-success" />
              {session.ended_at ? new Date(session.ended_at).toLocaleString() : "In Progress"}
            </span>
          </div>

          <div className="p-3 bg-bg-alt rounded-lg border border-border/60">
            <span className="text-text-secondary font-medium block">Created Date</span>
            <span className="text-text font-bold mt-1 flex items-center gap-1.5 text-sm">
              <Calendar size={14} className="text-accent" />
              {new Date(session.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </Card>

      {/* AI Assistant Ready Container (Day 60+ Future Ready) */}
      <Card className="p-8 border-accent/20 bg-gradient-to-br from-accent/5 via-bg to-bg relative overflow-hidden">
        <div className="max-w-md mx-auto text-center space-y-4">
          <div className="p-3.5 bg-accent/15 text-accent rounded-2xl w-fit mx-auto shadow-xs">
            <Bot size={32} />
          </div>

          <div className="space-y-1.5">
            <h3 className="text-lg font-bold text-text">
              Context-Aware AI Mentor Ready
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              This session is established as a persistent anchor for your learning journey. Future modules will enable persistent chat, automated AI summaries, and memory retrieval.
            </p>
          </div>

          {/* Future feature badges */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-[11px]">
            <span className="px-3 py-1 bg-bg border border-border rounded-full text-text-secondary font-medium flex items-center gap-1">
              <MessageSquare size={12} className="text-accent" /> Persistent Chat
            </span>
            <span className="px-3 py-1 bg-bg border border-border rounded-full text-text-secondary font-medium flex items-center gap-1">
              <Sparkles size={12} className="text-success" /> Session Summaries
            </span>
            <span className="px-3 py-1 bg-bg border border-border rounded-full text-text-secondary font-medium flex items-center gap-1">
              <Brain size={12} className="text-warning" /> AI Memory
            </span>
            <span className="px-3 py-1 bg-bg border border-border rounded-full text-text-secondary font-medium flex items-center gap-1">
              <Layers size={12} className="text-accent" /> RAG Pipeline
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
}
