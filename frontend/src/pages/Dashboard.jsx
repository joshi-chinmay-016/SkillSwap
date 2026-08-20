import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import Card from "../components/common/Card";
import SpotlightCard from "../components/common/SpotlightCard";
import SectionHeader from "../components/common/SectionHeader";
import EmptyState from "../components/common/EmptyState";
import PageTransition from "../components/common/PageTransition";
import Button from "../components/common/Button";
import Avatar from "../components/common/Avatar";
import { useStreak } from "../hooks/useStreak";
import HeatmapCard from "../components/dashboard/HeatmapCard";
import StreakCard from "../components/streak/StreakCard";
import MilestoneCard from "../components/streak/MilestoneCard";
import AnalyticsSection from "../components/analytics/AnalyticsSection";
import CredibilityBadge from "../components/verification/CredibilityBadge";
import { recommendationApi } from "../api/recommendationApi";

import {
  Calendar,
  Wallet as WalletIcon,
  ArrowRight,
  Sparkles,
  BookOpen,
  Award,
  ChevronRight,
  AlertCircle,
  Activity,
  CheckCircle2,
  Users,
  Compass,
  ShieldCheck,
  Zap,
  Target,
  ExternalLink,
  Flame,
} from "lucide-react";

export default function Dashboard() {
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();

  // 1. Fetch Profile info
  const { data: profile } = useQuery({
    queryKey: ["profile"],
    queryFn: async () => {
      const res = await api.get("/profiles/me");
      return res.data;
    },
  });

  // 2. Fetch User Skills
  const { data: userSkills = [], isLoading: isSkillsLoading } = useQuery({
    queryKey: ["userSkills"],
    queryFn: async () => {
      const res = await api.get("/skills/me");
      return res.data;
    },
  });

  // 3. Fetch Wallet balance
  const { data: wallet, isLoading: isWalletLoading } = useQuery({
    queryKey: ["wallet"],
    queryFn: async () => {
      const res = await api.get("/wallet/me");
      return res.data;
    },
    retry: false,
  });

  // 4. Fetch Upcoming Sessions
  const { data: upcomingSessions = [], isLoading: isSessionsLoading } = useQuery({
    queryKey: ["upcomingSessions"],
    queryFn: async () => {
      const res = await api.get("/sessions/upcoming");
      return res.data;
    },
  });

  // 5. Fetch Peer Recommendations (Real DB candidates)
  const { data: recommendations = [], isLoading: isRecsLoading } = useQuery({
    queryKey: ["recommendations", "hero"],
    queryFn: () => recommendationApi.getMyRecommendations(3),
  });

  // 6. Fetch Recent Learning Activities
  const { data: activityData, isLoading: isActivitiesLoading } = useQuery({
    queryKey: ["activities", "recent"],
    queryFn: async () => {
      const res = await api.get("/learning-activities/me", {
        params: { page: 1, size: 5 },
      });
      return res.data;
    },
  });

  const teachSkills = userSkills.filter((s) => s.type === "teach");
  const learnSkills = userSkills.filter((s) => s.type === "learn");

  return (
    <PageTransition className="space-y-8">
      {/* Hero Learning Command Banner with Whiteboard Corkboard Pushpin */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative overflow-visible rounded-3xl bg-card-bg border border-card-border p-6 sm:p-8 shadow-md"
      >
        <div className="absolute -top-3 left-8">
          <div className="w-5 h-5 rounded-full bg-amber-400 shadow-md border-2 border-white ring-1 ring-black/10 flex items-center justify-center relative">
            <div className="w-1.5 h-1.5 rounded-full bg-white/90 absolute top-0.5 left-1" />
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10 pt-1">
          <div className="flex items-center gap-4 sm:gap-5">
            <div className="relative shrink-0">
              <Avatar
                src={user?.avatar_url}
                alt={user?.name || "User"}
                size="xl"
                className="ring-4 ring-accent/20"
              />
              <div
                className="absolute -bottom-1 -right-1 bg-emerald-500 text-white rounded-full p-1 border-2 border-bg shadow-xs"
                title="Online & Ready to Learn"
              >
                <Zap size={12} className="fill-current" />
              </div>
            </div>
            <div className="text-left space-y-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-text">
                  Welcome back, {user?.name || "Learner"}!
                </h1>
                <span className="font-handwriting text-lg font-bold text-rose-500 rotate-[-3deg] inline-block">
                  Class is in session 📌
                </span>
              </div>
              <p className="text-xs sm:text-sm text-text-secondary font-medium">
                {profile?.department
                  ? `${profile.department} • Year ${profile.year}`
                  : "Learning Command Center • Active Peer Growth"}
              </p>
              {profile?.bio && (
                <p className="text-xs text-text-secondary italic line-clamp-1 max-w-lg mt-1">
                  &ldquo;{profile.bio}&rdquo;
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/profile")}
              leftIcon={ShieldCheck}
            >
              Verify Skills
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/mentors")}
              rightIcon={ArrowRight}
              className="shadow-glow"
            >
              Find Mentors
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Left 2 Columns (Main Learning Engine) */}
        <div className="lg:col-span-2 space-y-6 sm:space-y-8">
          {/* Peer Recommendations Section */}
          <Card
            title="Recommended Peers for You"
            subtitle="Compatibility matched using skill graphs and verified achievements"
            footer={
              recommendations.length > 0 && (
                <Link
                  to="/mentors"
                  className="text-accent font-bold text-xs hover:underline flex items-center gap-1"
                >
                  Explore all peer recommendations <ChevronRight size={14} />
                </Link>
              )
            }
          >
            {isRecsLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 py-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-32 bg-border/40 animate-pulse rounded-2xl" />
                ))}
              </div>
            ) : recommendations.length === 0 ? (
              <EmptyState
                icon={Users}
                title="No peer recommendations yet"
                description="Add target skills you wish to learn in Profile settings to receive automated peer matches."
                actionLabel="Configure Skills"
                onAction={() => navigate("/profile")}
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                {recommendations.slice(0, 3).map((rec) => (
                  <SpotlightCard
                    key={rec.mentor_id}
                    onClick={() => navigate(`/mentors/${rec.mentor_id}`)}
                    className="p-4 flex flex-col justify-between text-left space-y-3"
                  >
                    <div className="flex items-center gap-2.5">
                      <Avatar src={rec.avatar_url} alt={rec.mentor_name} size="md" />
                      <div className="min-w-0 flex-1">
                        <p className="font-bold text-xs text-text truncate">{rec.mentor_name}</p>
                        <p className="text-[10px] text-text-secondary truncate">
                          {rec.department || "Peer Mentor"}
                        </p>
                      </div>
                      <CredibilityBadge status={rec.verification_status} size="sm" />
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-text-secondary font-medium">Match</span>
                        <span className="font-bold text-accent">{rec.compatibility_score}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-accent to-purple-600 rounded-full transition-all duration-500"
                          style={{ width: `${rec.compatibility_score}%` }}
                        />
                      </div>
                    </div>

                    {rec.reasons && rec.reasons[0] && (
                      <p className="text-[10px] text-text-secondary line-clamp-1 italic bg-bg-alt/80 p-1.5 rounded-lg border border-border/50">
                        &ldquo;{rec.reasons[0]}&rdquo;
                      </p>
                    )}
                  </SpotlightCard>
                ))}
              </div>
            )}
          </Card>

          {/* Upcoming Sessions Widget */}
          <Card
            title="Upcoming Sessions"
            subtitle="Your scheduled 1-on-1 peer mentoring classes"
            footer={
              upcomingSessions.length > 0 && (
                <Link
                  to="/sessions"
                  className="text-accent font-bold text-xs hover:underline flex items-center gap-1"
                >
                  Manage all sessions <ChevronRight size={14} />
                </Link>
              )
            }
          >
            {isSessionsLoading ? (
              <div className="space-y-3 py-2">
                {[1, 2].map((i) => (
                  <div key={i} className="h-16 w-full bg-border/40 animate-pulse rounded-2xl" />
                ))}
              </div>
            ) : upcomingSessions.length === 0 ? (
              <EmptyState
                icon={Calendar}
                title="No upcoming sessions"
                description="Book your next learning or teaching session to advance your skill roadmap."
                actionLabel="Browse Mentors"
                onAction={() => navigate("/mentors")}
              />
            ) : (
              <div className="space-y-3">
                {upcomingSessions.map((session) => (
                  <div
                    key={session.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-bg border border-border rounded-2xl hover:border-accent/40 transition-all shadow-xs"
                  >
                    <div className="flex items-center gap-3 text-left">
                      <div className="w-10 h-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center font-bold text-sm border border-accent/20">
                        {session.mentor_name?.charAt(0) || "M"}
                      </div>
                      <div>
                        <p className="font-bold text-sm text-text">
                          {session.skill_name || "Mentoring Session"}
                        </p>
                        <p className="text-xs text-text-secondary mt-0.5">
                          with {session.mentor_name} •{" "}
                          {new Date(session.scheduled_at).toLocaleDateString()} at{" "}
                          {new Date(session.scheduled_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Link
                        to={`/learning-sessions/${session.id}`}
                        className="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-surface-elevated hover:bg-bg-alt border border-border transition-colors text-text"
                      >
                        Session Room
                      </Link>
                      {session.meeting_link && (
                        <a
                          href={session.meeting_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3.5 py-1.5 text-xs font-bold bg-accent text-white hover:bg-accent-hover rounded-xl shadow-xs transition-colors flex items-center gap-1"
                        >
                          <span>Join Call</span>
                          <ExternalLink size={12} />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Streak & Milestone Engine */}
          <StreakCard />
          {(() => {
            const { data, isLoading, isError } = useStreak();
            if (isLoading || isError || !data) return null;
            return (
              <MilestoneCard
                currentMilestone={data.current_milestone}
                nextMilestone={data.next_milestone}
                remainingDays={data.remaining_days}
                progressPercentage={data.progress_percentage}
              />
            );
          })()}

          {/* Learning Activity Heatmap */}
          <HeatmapCard />

          {/* Learning Analytics Intelligence */}
          <AnalyticsSection />

          {/* User Skills Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Skills You Offer" subtitle="What you can teach peers">
              {isSkillsLoading ? (
                <div className="h-20 bg-border/40 animate-pulse rounded-xl" />
              ) : teachSkills.length === 0 ? (
                <p className="text-xs text-text-secondary italic">
                  No teaching skills selected yet. Add your strengths in profile settings!
                </p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {teachSkills.map((s) => (
                    <span
                      key={s.id}
                      className="px-3 py-1 text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-full border border-emerald-500/20"
                    >
                      {s.skill?.name || s.name}
                    </span>
                  ))}
                </div>
              )}
            </Card>

            <Card title="Skills You Seek" subtitle="What you want to learn">
              {isSkillsLoading ? (
                <div className="h-20 bg-border/40 animate-pulse rounded-xl" />
              ) : learnSkills.length === 0 ? (
                <p className="text-xs text-text-secondary italic">
                  No learning goals configured. Add skills in Profile or AI Roadmap!
                </p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {learnSkills.map((s) => (
                    <span
                      key={s.id}
                      className="px-3 py-1 text-xs font-semibold bg-accent/10 text-accent rounded-full border border-accent/20"
                    >
                      {s.skill?.name || s.name}
                    </span>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>

        {/* Right Column (Wallet & AI Learning Core) */}
        <div className="space-y-6 sm:space-y-8">
          {/* Wallet Balance Hero */}
          <Card title="Skill Coins Wallet" subtitle="Swap coins to schedule 1-on-1 lessons">
            {isWalletLoading ? (
              <div className="h-24 bg-border/40 animate-pulse rounded-2xl" />
            ) : (
              <div className="flex items-center justify-between p-4 bg-bg border border-border rounded-2xl text-left">
                <div className="flex items-center gap-3.5">
                  <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-500 border border-amber-500/25 shadow-xs">
                    <WalletIcon size={24} />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-bold text-text-secondary tracking-wider">
                      Current Balance
                    </p>
                    <p className="text-2xl font-black text-text mt-0.5">
                      {wallet?.balance ?? "—"}{" "}
                      <span className="text-xs font-bold text-accent">Coins</span>
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => navigate("/wallet")}
                  className="px-2"
                >
                  <ChevronRight size={20} />
                </Button>
              </div>
            )}
            <p className="text-[11px] text-text-secondary mt-3 text-left leading-relaxed">
              Earn 5 coins when you teach a peer. Spend 5 coins to book a lesson with any peer mentor.
            </p>
          </Card>

          {/* AI Intelligence Hub */}
          <Card
            title="AI Learning Core"
            subtitle="Personalized guidance & roadmap builders"
            className="border-accent/30 bg-accent/[0.02]"
          >
            <div className="space-y-3 text-left">
              <button
                type="button"
                onClick={() => navigate("/mentor")}
                className="w-full flex items-start gap-3 p-3.5 rounded-2xl border border-border bg-bg hover:border-accent/40 cursor-pointer transition-all hover:-translate-y-0.5 shadow-xs"
              >
                <div className="p-2.5 bg-accent/10 text-accent rounded-xl border border-accent/20">
                  <Sparkles size={16} />
                </div>
                <div>
                  <h4 className="font-bold text-xs text-text flex items-center gap-1">
                    AI Learning Mentor <ArrowRight size={12} className="text-accent" />
                  </h4>
                  <p className="text-[11px] text-text-secondary mt-0.5">
                    Grounded answers based on uploaded engineering docs.
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => navigate("/journey/roadmap")}
                className="w-full flex items-start gap-3 p-3.5 rounded-2xl border border-border bg-bg hover:border-accent/40 cursor-pointer transition-all hover:-translate-y-0.5 shadow-xs"
              >
                <div className="p-2.5 bg-accent/10 text-accent rounded-xl border border-accent/20">
                  <Compass size={16} />
                </div>
                <div>
                  <h4 className="font-bold text-xs text-text flex items-center gap-1">
                    AI Roadmap Builder <ArrowRight size={12} className="text-accent" />
                  </h4>
                  <p className="text-[11px] text-text-secondary mt-0.5">
                    Generate step-by-step curriculum with milestones.
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => navigate("/journey/skill-gap")}
                className="w-full flex items-start gap-3 p-3.5 rounded-2xl border border-border bg-bg hover:border-accent/40 cursor-pointer transition-all hover:-translate-y-0.5 shadow-xs"
              >
                <div className="p-2.5 bg-accent/10 text-accent rounded-xl border border-accent/20">
                  <BookOpen size={16} />
                </div>
                <div>
                  <h4 className="font-bold text-xs text-text flex items-center gap-1">
                    Skill Gap Analyzer <ArrowRight size={12} className="text-accent" />
                  </h4>
                  <p className="text-[11px] text-text-secondary mt-0.5">
                    Benchmark your profile against target industry roles.
                  </p>
                </div>
              </button>
            </div>
          </Card>

          {/* Recent Activity Timeline */}
          <Card
            title="Recent Activity"
            subtitle="Your latest learning events"
            footer={
              activityData?.activities?.length > 0 && (
                <Link
                  to="/activity"
                  className="text-accent font-bold text-xs hover:underline flex items-center gap-1"
                >
                  View all activity history <ChevronRight size={14} />
                </Link>
              )
            }
          >
            {isActivitiesLoading ? (
              <div className="space-y-2.5 py-1">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-12 w-full bg-border/40 animate-pulse rounded-xl" />
                ))}
              </div>
            ) : !activityData?.activities?.length ? (
              <div className="py-6 text-center flex flex-col items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-bg-alt flex items-center justify-center text-text-secondary border border-border">
                  <Activity size={14} />
                </div>
                <div>
                  <p className="font-semibold text-xs text-text">No recent activity</p>
                  <p className="text-[10px] text-text-secondary mt-0.5">
                    Activities will appear here as you complete journey tasks.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {activityData.activities.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-center gap-3 p-2.5 bg-bg border border-border rounded-xl text-left"
                  >
                    <span className="text-sm shrink-0">
                      {activity.activity_type === "task_completed"
                        ? "✅"
                        : activity.activity_type === "milestone_completed"
                        ? "🏆"
                        : "🎯"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-xs text-text truncate">
                        {activity.activity_type === "task_completed"
                          ? "Task Completed"
                          : activity.activity_type === "milestone_completed"
                          ? "Milestone Achieved"
                          : "Learning Action"}
                      </p>
                      <p className="text-[10px] text-text-secondary mt-0.5">
                        {new Date(activity.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </PageTransition>
  );
}
