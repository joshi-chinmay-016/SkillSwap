import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "motion/react";
import api from "../services/api";
import MentorCard from "../components/MentorCard";
import Input from "../components/common/Input";
import Button from "../components/common/Button";
import Avatar from "../components/common/Avatar";
import SectionHeader from "../components/common/SectionHeader";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import PageTransition from "../components/common/PageTransition";
import SpotlightCard from "../components/common/SpotlightCard";
import CredibilityBadge from "../components/verification/CredibilityBadge";
import { recommendationApi } from "../api/recommendationApi";
import {
  Search,
  AlertCircle,
  Sparkles,
  Star,
  Lightbulb,
  UserCheck,
  Calendar,
  Filter,
  ArrowRight,
  SlidersHorizontal,
  X,
} from "lucide-react";
import SkillGapLoadingScreen from "../components/skill-gap/SkillGapLoadingScreen";

export default function MentorList() {
  const [searchQuery, setSearchQuery] = useState("");
  const [skillParam, setSkillParam] = useState("");
  const [minRating, setMinRating] = useState("");

  const navigate = useNavigate();

  // 1. Fetch Peer Mentor Recommendations
  const { data: recommendations = [], isLoading: isRecsLoading } = useQuery({
    queryKey: ["myRecommendations"],
    queryFn: () => recommendationApi.getMyRecommendations(6),
  });

  // 2. Fetch Mentors with search and rating filters
  const { data: mentors = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["mentors", skillParam, minRating],
    queryFn: async () => {
      const params = {};
      if (skillParam) params.skill = skillParam;
      if (minRating) params.min_rating = parseFloat(minRating);

      const res = await api.get("/mentors/", { params });
      return res.data;
    },
  });

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setSkillParam(searchQuery);
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setSkillParam("");
    setMinRating("");
  };

  return (
    <PageTransition className="space-y-8 text-left">
      {/* Section Header */}
      <SectionHeader
        badge="Peer Network Discovery"
        badgeIcon={UserCheck}
        title="Discover Peer Mentors"
        subtitle="Connect with verified student peers, analyze compatibility signals, and book 1-on-1 skill swap sessions."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate("/ai/mentor-recommendation")}
            leftIcon={Sparkles}
            className="shadow-glow"
          >
            AI Matching Assistant
          </Button>
        }
      />

      {/* Recommended Peers for You Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-accent" />
            <h2 className="text-base sm:text-lg font-bold tracking-tight text-text">
              Recommended Peers for You
            </h2>
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
              Evidence-Based
            </span>
          </div>
        </div>

        {isRecsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-border/40 animate-pulse rounded-2xl" />
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <EmptyState
            icon={UserCheck}
            title="No recommendations available yet"
            description="Add skills you want to learn in your profile to receive personalized peer recommendations."
            actionLabel="Add Skills in Profile"
            onAction={() => navigate("/profile")}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((rec) => (
              <SpotlightCard
                key={rec.mentor_id}
                onClick={() =>
                  navigate(`/mentors/${rec.mentor_id}`, {
                    state: { mentorName: rec.mentor_name, averageRating: rec.average_rating },
                  })
                }
                className="p-5 flex flex-col justify-between space-y-3 cursor-pointer group"
              >
                <div className="space-y-3">
                  {/* Top Bar: Avatar & Match Score */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <Avatar
                        src={rec.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${rec.mentor_name}`}
                        alt={rec.mentor_name}
                        size="md"
                        className="ring-2 ring-accent/20 shrink-0"
                      />
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-bold text-text truncate group-hover:text-accent transition-colors">
                          {rec.mentor_name}
                        </h3>
                        <p className="text-xs text-text-secondary truncate">
                          {rec.department ? `${rec.department}` : "Student"} {rec.year ? `• Year ${rec.year}` : ""}
                        </p>
                      </div>
                    </div>

                    <div className="px-2.5 py-1 rounded-full bg-accent/15 border border-accent/25 text-accent font-extrabold text-xs shrink-0">
                      {Math.round(rec.compatibility_score)}% Match
                    </div>
                  </div>

                  {/* Rating & Credibility */}
                  <div className="flex items-center gap-2 flex-wrap text-xs">
                    <CredibilityBadge status={rec.verification_status} score={rec.credibility_score} size="sm" />
                    {rec.average_rating > 0 && (
                      <span className="flex items-center gap-1 font-bold text-amber-500">
                        <Star size={13} className="fill-amber-500" />
                        <span className="text-text">{rec.average_rating.toFixed(1)}</span>
                        <span className="text-text-secondary font-normal">({rec.feedback_count})</span>
                      </span>
                    )}
                    {rec.availability && (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                        <Calendar size={12} /> Available
                      </span>
                    )}
                  </div>

                  {/* Evidence Reasons */}
                  {rec.reasons && rec.reasons.length > 0 && (
                    <div className="p-2.5 rounded-xl bg-bg-alt/80 border border-border/60 text-[11px] space-y-1">
                      {rec.reasons.slice(0, 2).map((reason, idx) => (
                        <div key={idx} className="flex items-start gap-1.5 text-text-secondary">
                          <Lightbulb size={13} className="text-accent shrink-0 mt-0.5" />
                          <span className="leading-tight font-medium">{reason}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-3 text-xs font-bold text-accent flex items-center justify-between border-t border-border/60">
                  <span>View Profile & Book Session</span>
                  <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
                </div>
              </SpotlightCard>
            ))}
          </div>
        )}
      </div>

      <div className="w-full h-px bg-border/80" />

      {/* Search and Filters Bar */}
      <div className="bg-card-bg border border-card-border p-5 rounded-2xl shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="flex-1 relative">
            <Input
              type="text"
              placeholder="Search skills (e.g. React, Python, FastAPI, UI/UX, System Design)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="w-full md:w-48 flex flex-col gap-1 text-left">
            <select
              value={minRating}
              onChange={(e) => setMinRating(e.target.value)}
              className="w-full h-[40px] px-3.5 py-2 text-xs font-semibold rounded-xl border border-border bg-bg text-text shadow-xs focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent cursor-pointer"
            >
              <option value="">All Ratings</option>
              <option value="4.5">★ 4.5 & up</option>
              <option value="4.0">★ 4.0 & up</option>
              <option value="3.0">★ 3.0 & up</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button type="submit" variant="primary" className="h-[40px] px-6 font-bold shadow-xs">
              <Search size={15} className="mr-1" /> Search
            </Button>
            {(skillParam || minRating) && (
              <Button
                type="button"
                variant="outline"
                onClick={handleClearFilters}
                className="h-[40px] text-xs font-semibold"
                leftIcon={X}
              >
                Clear
              </Button>
            )}
          </div>
        </form>
      </div>

      {/* All Mentors List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base sm:text-lg font-bold tracking-tight text-text">
            All Peer Mentors ({mentors.length})
          </h2>
        </div>

        {isLoading && <SkillGapLoadingScreen isOpen={true} onCancel={() => refetch()} />}

        {isError ? (
          <ErrorState
            title="Failed to load mentors"
            message="We encountered an issue fetching peer mentor profiles. Please check your backend connection."
            onRetry={() => refetch()}
          />
        ) : mentors.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No mentors match these criteria"
            description={`We couldn't find any mentors matching "${skillParam || searchQuery}". Try adjusting filters or searching for another skill.`}
            actionLabel="Clear Filters"
            onAction={handleClearFilters}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-7">
            {mentors.map((mentor, index) => {
              const pinColors = ["red", "cyan", "yellow", "purple", "green"];
              return (
                <MentorCard
                  key={mentor.mentor_id || mentor.id}
                  mentor={mentor}
                  index={index}
                  pinColor={pinColors[index % pinColors.length]}
                  sway={index % 2 === 0 ? "left" : "right"}
                  onClick={() =>
                    navigate(`/mentors/${mentor.mentor_id || mentor.id}`, {
                      state: { mentorName: mentor.mentor_name || mentor.name, averageRating: mentor.average_rating },
                    })
                  }
                />
              );
            })}
          </div>
        )}
      </div>
    </PageTransition>
  );
}
