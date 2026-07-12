import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import ProgressBar from "../components/common/ProgressBar";
import Skeleton, { SkeletonCard } from "../components/common/Skeleton";
import { useToast } from "../components/common/Toast";
import { Compass, Users, Sparkles, BookOpen, Target, Clock, ArrowLeft, Calendar, Award, CheckCircle, Circle, AlertCircle, ArrowUp, ArrowDown } from "lucide-react";

export default function LearningJourney() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [selectedMilestone, setSelectedMilestone] = useState(null);

  const { data: journey, isLoading, error } = useQuery({
    queryKey: ["journey", id],
    queryFn: async () => {
      const res = await api.get(`/journeys/${id}`);
      return res.data;
    },
    retry: false,
  });

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case "active":
        return "bg-success/10 text-success border-success/20";
      case "paused":
        return "bg-warning/10 text-warning border-warning/20";
      case "completed":
        return "bg-accent/10 text-accent border-accent/20";
      case "archived":
        return "bg-danger/10 text-danger border-danger/20";
      default:
        return "bg-border/40 text-text-secondary border-border/20";
    }
  };

  const getMilestoneStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return "bg-success/15 text-success border-success/20";
      case "in_progress":
        return "bg-accent/15 text-accent border-accent/20";
      case "pending":
      default:
        return "bg-bg-alt text-text-secondary border-border";
    }
  };

  // Loading state skeleton
  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-4">
          <Skeleton variant="rectangular" width="120px" height="32px" />
          <div className="flex-1">
            <Skeleton variant="text" width="60%" height="28px" />
            <Skeleton variant="text" width="40%" height="16px" className="mt-1" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 bg-bg-alt border border-border rounded-lg space-y-2">
                <Skeleton variant="text" width="30%" height="20px" />
                <Skeleton variant="text" width="80%" height="14px" />
              </div>
            ))}
          </div>
          <div className="space-y-4">
            <div className="p-4 bg-bg-alt border border-border rounded-lg space-y-2">
              <Skeleton variant="text" width="50%" height="18px" />
              <Skeleton variant="rectangular" width="100%" height="10px" className="mt-2" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error handling
  if (error) {
    const status = error.response?.status;
    let title = "Failed to load journey";
    let message = "We encountered an error retrieving this learning journey. Please try again.";

    if (status === 403) {
      title = "Access Denied";
      message = "You do not have permission to view or manage this learning journey.";
    } else if (status === 404) {
      title = "Journey Not Found";
      message = "The requested learning journey does not exist or has been deleted.";
    }

    return (
      <div className="max-w-md mx-auto mt-12">
        <Card className="text-center py-8">
          <div className="p-3 bg-danger/10 text-danger rounded-full w-fit mx-auto mb-4">
            <AlertCircle size={32} />
          </div>
          <h2 className="text-lg font-bold text-text">{title}</h2>
          <p className="text-sm text-text-secondary mt-2 px-4">{message}</p>
          <div className="mt-6 flex flex-col gap-2 px-4">
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/journey/roadmap")}
            >
              <Compass size={16} className="mr-2" />
              Go to Roadmap Builder
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!journey) {
    return (
      <div className="max-w-md mx-auto mt-12">
        <Card className="text-center py-8">
          <div className="p-3 bg-border/40 text-text-secondary rounded-full w-fit mx-auto mb-4">
            <Compass size={32} />
          </div>
          <h2 className="text-lg font-bold text-text">No active journey found</h2>
          <p className="text-sm text-text-secondary mt-2 px-4">Please build an AI roadmap and save it first.</p>
          <div className="mt-6">
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/journey/roadmap")}
            >
              Build New Roadmap
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header Area */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-2">
          <button
            onClick={() => navigate("/journey/roadmap")}
            className="flex items-center text-xs font-semibold text-text-secondary hover:text-accent w-fit transition-colors gap-1 group animate-in slide-in-from-left duration-200"
          >
            <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
            Back to Roadmaps
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-text">{journey.title}</h1>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(journey.status)}`}>
              {journey.status}
            </span>
          </div>
          <p className="text-sm text-text-secondary flex items-center gap-1.5 mt-0.5">
            <Target size={14} className="text-accent" />
            Target: <span className="font-semibold text-text">{journey.target_role}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/journey/roadmap?new=true")}
          >
            <Sparkles size={14} className="mr-1.5" />
            Build New Journey
          </Button>
        </div>
      </div>

      {/* Main Body Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Milestones / Week Timeline (Colspan 2) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <h2 className="text-base font-bold text-text px-1">Learning Milestones</h2>
          
          <div className="flex flex-col gap-3">
            {journey.milestones?.map((milestone) => {
              const isSelected = selectedMilestone === milestone.id;
              return (
                <div
                  key={milestone.id}
                  className={`border rounded-lg bg-bg transition-all ${
                    isSelected ? "border-accent/40 shadow-sm" : "border-border hover:shadow-xs"
                  }`}
                >
                  {/* Summary / Header */}
                  <div
                    onClick={() => setSelectedMilestone(isSelected ? null : milestone.id)}
                    className="flex items-start gap-4 p-4 cursor-pointer select-none"
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm border ${
                        milestone.status === "completed" 
                          ? "bg-success/10 text-success border-success/30" 
                          : "bg-bg-alt text-text-secondary border-border"
                      }`}>
                        {milestone.week_number}
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <h4 className="font-semibold text-text text-sm truncate">
                          Week {milestone.week_number}: {milestone.topic}
                        </h4>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border shrink-0 ${getMilestoneStatusColor(milestone.status)}`}>
                          {milestone.status}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary mt-1 line-clamp-1">
                        {milestone.goal}
                      </p>
                    </div>

                    <div className="text-text-secondary self-center shrink-0">
                      {isSelected ? <ArrowUp size={16} /> : <ArrowDown size={16} />}
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isSelected && (
                    <div className="px-4 pb-4 pt-2 border-t border-border/60 bg-bg-alt/30 text-xs text-text-secondary space-y-4">
                      <div>
                        <h5 className="font-bold text-text text-[11px] uppercase tracking-wider mb-1">Weekly Goal</h5>
                        <p className="text-text-secondary leading-relaxed bg-bg border border-border p-3 rounded-md">
                          {milestone.goal}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-border/40">
                        <Button 
                          variant="outline" 
                          size="xs"
                          onClick={() => navigate(`/mentors?role=${encodeURIComponent(journey.target_role)}`)}
                        >
                          <Users size={12} className="mr-1.5" />
                          Find Mentor for Help
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {(!journey.milestones || journey.milestones.length === 0) && (
              <Card className="text-center py-8 text-text-secondary italic">
                No milestones in this journey.
              </Card>
            )}
          </div>
        </div>

        {/* Stats and Info Sidebar */}
        <div className="flex flex-col gap-6">
          
          {/* Progress Overview Card */}
          <Card title="Journey Progress" subtitle="Milestone Completion Tracker">
            <div className="space-y-4">
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-text">
                  {Math.round(journey.progress_percentage)}%
                </span>
                <span className="text-xs text-text-secondary">
                  Week {journey.current_week} of {journey.total_weeks}
                </span>
              </div>
              <ProgressBar value={journey.progress_percentage} size="md" animated />
              <p className="text-xs text-text-secondary leading-relaxed">
                Your progress is calculated based on milestone tasks completed. Swap skills with mentors to accelerate your growth.
              </p>
            </div>
          </Card>

          {/* Details Sidebar Card */}
          <Card title="Journey Details">
            <div className="space-y-4 text-xs">
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-text-secondary font-medium">Duration</span>
                <span className="text-text font-bold flex items-center gap-1">
                  <Clock size={12} className="text-accent" />
                  {journey.duration_months || 0} Months
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-text-secondary font-medium">Created On</span>
                <span className="text-text font-bold flex items-center gap-1">
                  <Calendar size={12} className="text-accent" />
                  {new Date(journey.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-text-secondary font-medium">Last Activity</span>
                <span className="text-text font-bold">
                  {new Date(journey.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </Card>

        </div>
      </div>
    </div>
  );
}
