import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../services/api";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import { Calendar, Video, Clock, CheckCircle, XCircle, AlertCircle, MessageSquare } from "lucide-react";

export default function Sessions() {
  const [activeTab, setActiveTab] = useState("upcoming");
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Fetch upcoming sessions
  const {
    data: upcoming = [],
    isLoading: isUpcomingLoading,
    isError: isUpcomingError,
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
  } = useQuery({
    queryKey: ["completedSessions"],
    queryFn: async () => {
      const res = await api.get("/sessions/completed");
      return res.data;
    },
  });

  // Complete session mutation
  const completeMutation = useMutation({
    mutationFn: async (sessionId) => {
      const res = await api.patch(`/sessions/${sessionId}/complete`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["upcomingSessions"]);
      queryClient.invalidateQueries(["completedSessions"]);
    },
  });

  // Cancel session mutation
  const cancelMutation = useMutation({
    mutationFn: async (sessionId) => {
      const res = await api.patch(`/sessions/${sessionId}/cancel`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["upcomingSessions"]);
    },
  });

  const isLoading = activeTab === "upcoming" ? isUpcomingLoading : isCompletedLoading;
  const isError = activeTab === "upcoming" ? isUpcomingError : isCompletedError;
  const sessionsList = activeTab === "upcoming" ? upcoming : completed;

  return (
    <div className="flex flex-col gap-6 text-left">
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-bold tracking-tight text-text m-0">
          Your Sessions
        </h1>
        <p className="text-xs text-text-secondary mt-1">
          Manage your booked learning swaps and view past lesson history summaries
        </p>
      </div>

      {/* Tabs Switcher */}
      <div className="flex border-b border-border">
        <button
          type="button"
          onClick={() => setActiveTab("upcoming")}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === "upcoming"
              ? "border-accent text-accent"
              : "border-transparent text-text-secondary hover:text-text"
          }`}
        >
          Upcoming Sessions ({upcoming.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("completed")}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === "completed"
              ? "border-accent text-accent"
              : "border-transparent text-text-secondary hover:text-text"
          }`}
        >
          Completed Swaps ({completed.length})
        </button>
      </div>

      {/* Content list */}
      {isLoading ? (
        <div className="flex flex-col gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-28 w-full bg-border/40 animate-pulse rounded-lg border border-border" />
          ))}
        </div>
      ) : isError ? (
        <div className="py-12 bg-bg border border-border rounded-xl flex flex-col items-center gap-2 text-center">
          <AlertCircle className="text-danger" size={32} />
          <p className="font-semibold text-sm">Failed to load sessions</p>
          <p className="text-xs text-text-secondary">Please check your server connection.</p>
        </div>
      ) : sessionsList.length === 0 ? (
        <div className="py-16 bg-bg border border-border rounded-xl flex flex-col items-center gap-3 text-center">
          <div className="w-12 h-12 rounded-full bg-bg-alt flex items-center justify-center text-text-secondary border border-border">
            <Calendar size={20} />
          </div>
          <p className="font-semibold text-sm">
            {activeTab === "upcoming" ? "No upcoming sessions scheduled" : "No completed sessions yet"}
          </p>
          <p className="text-xs text-text-secondary max-w-sm">
            {activeTab === "upcoming"
              ? "Schedule a mentoring call with a student peer. Search mentors to get started."
              : "Completed sessions will show up here along with your AI recap summaries."}
          </p>
          {activeTab === "upcoming" && (
            <Button size="sm" variant="primary" onClick={() => navigate("/mentors")} className="mt-2">
              Discover Mentors
            </Button>
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {sessionsList.map((session) => (
            <Card
              key={session.id}
              className="bg-bg border border-border hover:shadow-xs transition-shadow"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                {/* Details info */}
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center font-bold text-sm shrink-0">
                    {session.mentor_name?.charAt(0) || "S"}
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-text">
                      {session.skill_name || "Mentoring Session"}
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">
                      {activeTab === "upcoming" ? "Mentor:" : "Swapped with:"} <span className="font-semibold text-text">{session.mentor_name}</span>
                    </p>
                    
                    {/* Time */}
                    <div className="flex items-center gap-3 text-[11px] text-text-secondary mt-2">
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {new Date(session.scheduled_at).toLocaleDateString()} at{" "}
                        {new Date(session.scheduled_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions button */}
                <div className="flex flex-wrap items-center gap-2 sm:self-center">
                  {activeTab === "upcoming" ? (
                    <>
                      <a
                        href={session.meeting_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold bg-accent text-white hover:bg-accent-hover rounded-md shadow-xs transition-colors"
                      >
                        <Video size={14} /> Join Call
                      </a>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => completeMutation.mutate(session.id)}
                        isLoading={completeMutation.isPending}
                        className="text-green-600 border-green-500/20 hover:bg-green-500/10"
                      >
                        <CheckCircle size={14} /> Complete
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => cancelMutation.mutate(session.id)}
                        isLoading={cancelMutation.isPending}
                        className="text-danger hover:bg-danger/10"
                      >
                        <XCircle size={14} /> Cancel
                      </Button>
                    </>
                  ) : (
                    <Link
                      to={`/sessions/${session.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold bg-bg-alt border border-border text-text hover:bg-border rounded-md transition-colors"
                    >
                      <MessageSquare size={14} className="text-accent" />
                      View AI Summary & Notes
                    </Link>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
