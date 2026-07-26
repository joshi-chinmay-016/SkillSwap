import React, { useState } from "react";
import {
  useJourneySessions,
  useCreateSession,
  useCompleteSession,
  useArchiveSession,
} from "../../hooks/useSessions";
import SessionCard from "./SessionCard";
import CreateSessionModal from "./CreateSessionModal";
import EmptySessions from "./EmptySessions";
import Card from "../common/Card";
import Button from "../common/Button";
import Skeleton from "../common/Skeleton";
import { useToast } from "../common/Toast";
import { Sparkles, Plus, AlertCircle, CheckCircle2, Archive, Loader2, RefreshCw } from "lucide-react";

/**
 * JourneySessions Component
 * Comprehensive session management list component for a Learning Journey.
 */
export default function JourneySessions({ journeyId }) {
  const toast = useToast();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [sessionToComplete, setSessionToComplete] = useState(null);
  const [sessionToArchive, setSessionToArchive] = useState(null);

  // Queries & Mutations
  const {
    data: sessionsData,
    isLoading,
    isError,
    refetch,
  } = useJourneySessions(journeyId);

  const createSessionMutation = useCreateSession(journeyId);
  const completeSessionMutation = useCompleteSession(journeyId);
  const archiveSessionMutation = useArchiveSession(journeyId);

  const sessions = sessionsData?.sessions || [];

  // Handlers
  const handleCreateSession = (formData) => {
    createSessionMutation.mutate(formData, {
      onSuccess: (newSession) => {
        setIsCreateModalOpen(false);
        toast.show(`Session "${newSession.title}" created successfully! ✨`, "success");
      },
      onError: (err) => {
        toast.show(
          err.response?.data?.detail || "Failed to create learning session.",
          "error"
        );
      },
    });
  };

  const handleConfirmComplete = () => {
    if (!sessionToComplete) return;

    completeSessionMutation.mutate(sessionToComplete.id, {
      onSuccess: (data) => {
        setSessionToComplete(null);
        toast.show(
          `Session completed! 🎯 Activity logged & achievements updated.`,
          "success"
        );
      },
      onError: (err) => {
        toast.show(
          err.response?.data?.detail || "Failed to complete session.",
          "error"
        );
      },
    });
  };

  const handleConfirmArchive = () => {
    if (!sessionToArchive) return;

    archiveSessionMutation.mutate(sessionToArchive.id, {
      onSuccess: () => {
        setSessionToArchive(null);
        toast.show("Session archived.", "info");
      },
      onError: (err) => {
        toast.show(
          err.response?.data?.detail || "Failed to archive session.",
          "error"
        );
      },
    });
  };

  return (
    <div className="space-y-4">
      {/* Section Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-text flex items-center gap-2">
            <Sparkles size={18} className="text-accent" />
            Learning Sessions
          </h2>
          <p className="text-xs text-text-secondary mt-0.5">
            Interactive AI learning sessions for this journey
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => setIsCreateModalOpen(true)}
          className="shadow-xs"
        >
          <Plus size={16} className="mr-1" />
          Create Session
        </Button>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="p-4 border border-border bg-bg rounded-xl space-y-3">
              <div className="flex justify-between items-center">
                <Skeleton variant="text" width="60%" height="20px" />
                <Skeleton variant="rectangular" width="70px" height="22px" className="rounded-full" />
              </div>
              <Skeleton variant="text" width="40%" height="14px" />
              <div className="pt-2 flex justify-between items-center border-t border-border/40">
                <Skeleton variant="text" width="30%" height="12px" />
                <Skeleton variant="rectangular" width="80px" height="28px" className="rounded-md" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && !isLoading && (
        <Card className="text-center py-8 px-6 border-danger/30 bg-danger/5">
          <div className="flex flex-col items-center">
            <AlertCircle size={32} className="text-danger mb-2" />
            <h3 className="text-sm font-bold text-text">Unable to load sessions</h3>
            <p className="text-xs text-text-secondary mt-1">
              We encountered a temporary issue retrieving your learning sessions.
            </p>
            <Button
              variant="outline"
              size="xs"
              onClick={() => refetch()}
              className="mt-4"
            >
              <RefreshCw size={14} className="mr-1.5" />
              Retry
            </Button>
          </div>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !isError && sessions.length === 0 && (
        <EmptySessions onCreateClick={() => setIsCreateModalOpen(true)} />
      )}

      {/* Sessions Grid */}
      {!isLoading && !isError && sessions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onComplete={(s) => setSessionToComplete(s)}
              onArchive={(s) => setSessionToArchive(s)}
            />
          ))}
        </div>
      )}

      {/* Create Session Modal */}
      <CreateSessionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateSession}
        isSubmitting={createSessionMutation.isPending}
      />

      {/* Complete Confirmation Modal */}
      {sessionToComplete && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-150"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-sm bg-bg border border-border rounded-xl p-6 shadow-xl space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-success/10 text-success rounded-full">
                <CheckCircle2 size={24} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text">Complete Learning Session?</h3>
                <p className="text-xs text-text-secondary mt-0.5">
                  "{sessionToComplete.title}"
                </p>
              </div>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed bg-bg-alt p-3 rounded-lg border border-border/60">
              Completing this session will record a Learning Activity, update your heatmaps, streak, and trigger achievement evaluation. This action cannot be undone.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSessionToComplete(null)}
                disabled={completeSessionMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmComplete}
                disabled={completeSessionMutation.isPending}
                className="bg-success hover:bg-success/90 text-white border-none"
              >
                {completeSessionMutation.isPending ? (
                  <>
                    <Loader2 size={14} className="mr-1.5 animate-spin" />
                    Completing...
                  </>
                ) : (
                  "Complete"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Archive Confirmation Modal */}
      {sessionToArchive && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-150"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-sm bg-bg border border-border rounded-xl p-6 shadow-xl space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-warning/10 text-warning rounded-full">
                <Archive size={24} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text">Archive Learning Session?</h3>
                <p className="text-xs text-text-secondary mt-0.5">
                  "{sessionToArchive.title}"
                </p>
              </div>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed bg-bg-alt p-3 rounded-lg border border-border/60">
              Archived sessions remain visible in your history, but cannot be continued or completed.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSessionToArchive(null)}
                disabled={archiveSessionMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmArchive}
                disabled={archiveSessionMutation.isPending}
                className="bg-text-secondary hover:bg-text text-bg border-none"
              >
                {archiveSessionMutation.isPending ? (
                  <>
                    <Loader2 size={14} className="mr-1.5 animate-spin" />
                    Archiving...
                  </>
                ) : (
                  "Archive"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
