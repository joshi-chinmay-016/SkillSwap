import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api";
import MentorCard from "../components/MentorCard";
import Input from "../components/common/Input";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import Avatar from "../components/common/Avatar";
import CredibilityBadge from "../components/verification/CredibilityBadge";
import { recommendationApi } from "../api/recommendationApi";
import { Search, AlertCircle, Sparkles, Star, Lightbulb, UserCheck, Calendar } from "lucide-react";
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
    <div className="flex flex-col gap-6 text-left">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-text m-0">
            Find a Peer Mentor
          </h1>
          <p className="text-xs text-text-secondary mt-1">
            Discover student mentors, view verified skills, and request 1-on-1 swap sessions
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate("/ai/mentor-recommendation")}
          className="shrink-0"
        >
          <Sparkles size={14} className="mr-1.5" />
          AI Matching Assistant
        </Button>
      </div>

      {/* Real "Recommended for You" Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold tracking-tight text-text flex items-center gap-1.5">
              <Sparkles size={18} className="text-accent" /> Recommended for You
            </h2>
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
              Evidence-Based Matching
            </span>
          </div>
        </div>

        {isRecsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-44 bg-border/40 animate-pulse rounded-xl" />
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <div className="p-5 bg-bg/50 border border-border rounded-xl flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-full bg-accent/10 text-accent shrink-0">
                <UserCheck size={20} />
              </div>
              <div>
                <p className="text-sm font-bold text-text">No recommendations available yet</p>
                <p className="text-xs text-text-secondary">
                  Add skills you want to learn in your profile to receive personalized peer recommendations.
                </p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate("/profile")}>
              Add Skills in Profile
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((rec) => (
              <div
                key={rec.mentor_id}
                onClick={() =>
                  navigate(`/mentors/${rec.mentor_id}`, {
                    state: { mentorName: rec.mentor_name, averageRating: rec.average_rating },
                  })
                }
                className="p-4 bg-bg border border-border hover:border-accent/50 rounded-xl transition-all shadow-xs hover:shadow-md cursor-pointer flex flex-col justify-between space-y-3 group"
              >
                <div>
                  {/* Top Bar: Avatar, Info & Match Score */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <Avatar
                        src={rec.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${rec.mentor_name}`}
                        alt={rec.mentor_name}
                        size="md"
                      />
                      <div>
                        <h3 className="text-sm font-bold text-text group-hover:text-accent transition-colors">
                          {rec.mentor_name}
                        </h3>
                        <p className="text-xs text-text-secondary">
                          {rec.department ? `${rec.department}` : "Student"} {rec.year ? `• Year ${rec.year}` : ""}
                        </p>
                      </div>
                    </div>

                    <div className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent font-extrabold text-xs shrink-0">
                      {Math.round(rec.compatibility_score)}% Match
                    </div>
                  </div>

                  {/* Rating & Credibility */}
                  <div className="flex items-center gap-2 mt-3 flex-wrap text-xs">
                    <CredibilityBadge status={rec.verification_status} score={rec.credibility_score} size="sm" />
                    {rec.average_rating > 0 && (
                      <span className="flex items-center gap-1 font-semibold text-text">
                        <Star size={12} className="text-amber-500 fill-amber-500" />
                        {rec.average_rating.toFixed(1)} ({rec.feedback_count})
                      </span>
                    )}
                    {rec.availability && (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                        <Calendar size={12} /> Available
                      </span>
                    )}
                  </div>

                  {/* Evidence Reasons List */}
                  {rec.reasons && rec.reasons.length > 0 && (
                    <div className="mt-3 p-2.5 rounded-lg bg-bg-alt/60 border border-border/50 text-[11px] space-y-1">
                      {rec.reasons.slice(0, 2).map((reason, idx) => (
                        <div key={idx} className="flex items-start gap-1.5 text-text-secondary">
                          <Lightbulb size={12} className="text-accent shrink-0 mt-0.5" />
                          <span className="leading-tight">{reason}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-2 text-xs font-semibold text-accent flex items-center justify-between border-t border-border/40">
                  <span>View Profile & Book Session</span>
                  <span>→</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="w-full h-px bg-border my-1" />

      {/* Search and Filters Bar */}
      <div className="bg-bg border border-border p-4 rounded-lg shadow-xs">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="flex-1 relative">
            <Input
              type="text"
              placeholder="Search all skills (e.g. React, Python, UI/UX)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="w-full md:w-48 flex flex-col gap-1 text-left">
            <select
              value={minRating}
              onChange={(e) => setMinRating(e.target.value)}
              className="w-full h-[38px] px-3 py-2 text-sm rounded-md border border-border bg-bg text-text shadow-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent cursor-pointer"
            >
              <option value="">All Ratings</option>
              <option value="4.5">★ 4.5 & up</option>
              <option value="4.0">★ 4.0 & up</option>
              <option value="3.0">★ 3.0 & up</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button type="submit" variant="primary" className="h-[38px] px-5">
              <Search size={16} /> Search
            </Button>
            {(skillParam || minRating) && (
              <Button type="button" variant="outline" onClick={handleClearFilters} className="h-[38px]">
                Clear
              </Button>
            )}
          </div>
        </form>
      </div>

      {/* All Mentors List */}
      <div>
        <h2 className="text-base font-bold tracking-tight text-text mb-3">All Peer Mentors</h2>
        {isLoading && <SkillGapLoadingScreen isOpen={true} onCancel={() => refetch()} />}
        {isError ? (
          <div className="py-12 bg-bg border border-border rounded-xl flex flex-col items-center gap-2">
            <AlertCircle className="text-danger" size={32} />
            <p className="font-semibold text-sm">Failed to load mentors</p>
            <p className="text-xs text-text-secondary">Please check your backend server connection.</p>
            <Button size="sm" variant="outline" onClick={() => refetch()} className="mt-2">
              Retry
            </Button>
          </div>
        ) : mentors.length === 0 ? (
          <div className="py-16 bg-bg border border-border rounded-xl flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-bg-alt flex items-center justify-center text-text-secondary border border-border">
              <Search size={20} />
            </div>
            <p className="font-semibold text-sm">No mentors found</p>
            <p className="text-xs text-text-secondary max-w-sm text-center">
              We couldn't find any mentors matching "{skillParam || searchQuery}". Try searching for another skill or clearing filters.
            </p>
            <Button size="sm" variant="outline" onClick={handleClearFilters} className="mt-2">
              Clear Filters
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mentors.map((mentor) => (
              <MentorCard
                key={mentor.mentor_id}
                mentor={mentor}
                onClick={() =>
                  navigate(`/mentors/${mentor.mentor_id}`, {
                    state: { mentorName: mentor.mentor_name, averageRating: mentor.average_rating },
                  })
                }
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
