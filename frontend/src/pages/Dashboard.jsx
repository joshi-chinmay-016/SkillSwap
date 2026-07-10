import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Avatar from "../components/common/Avatar";
import {
  Calendar,
  Wallet as WalletIcon,
  ArrowRight,
  Sparkles,
  BookOpen,
  Award,
  ChevronRight,
  AlertCircle
} from "lucide-react";

export default function Dashboard() {
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();

  // 1. Fetch Profile info (bio, department, year, etc.)
  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: async () => {
      const res = await api.get("/profiles/me");
      return res.data;
    },
  });

  // 2. Fetch User Skills (to show teach and learn lists)
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
    retry: false, // Don't throw errors in console if wallet tables are not fully migrated
  });

  // 4. Fetch Upcoming Sessions
  const { data: upcomingSessions = [], isLoading: isSessionsLoading } = useQuery({
    queryKey: ["upcomingSessions"],
    queryFn: async () => {
      const res = await api.get("/sessions/upcoming");
      return res.data;
    },
  });

  const teachSkills = userSkills.filter((s) => s.type === "teach");
  const learnSkills = userSkills.filter((s) => s.type === "learn");

  return (
    <div className="flex flex-col gap-6">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-bg border border-border p-6 rounded-xl shadow-xs">
        <div className="flex items-center gap-4">
          <Avatar src={user?.avatar_url} alt={user?.name || "User"} size="xl" />
          <div className="text-left">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-text m-0">
              Welcome back, {user?.name || "Learner"}!
            </h1>
            <p className="text-xs text-text-secondary mt-1">
              {profile?.department ? `${profile.department} Student (Year ${profile.year})` : "Set up your department in Profile Settings"}
            </p>
            {profile?.bio && (
              <p className="text-xs text-text-secondary italic mt-1.5 line-clamp-1">
                "{profile.bio}"
              </p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate("/profile")}>
            Edit Profile
          </Button>
          <Button variant="primary" size="sm" onClick={() => navigate("/mentors")}>
            Find Mentors
          </Button>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (Main Stats & Sessions) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Upcoming Sessions Widget */}
          <Card
            title="Upcoming Sessions"
            subtitle="Your scheduled peer-to-peer mentoring classes"
            footer={
              upcomingSessions.length > 0 && (
                <Link to="/sessions" className="text-accent font-semibold hover:underline flex items-center gap-1">
                  View all sessions <ChevronRight size={14} />
                </Link>
              )
            }
          >
            {isSessionsLoading ? (
              <div className="flex flex-col gap-3 py-2">
                {[1, 2].map((i) => (
                  <div key={i} className="h-16 w-full bg-border/40 animate-pulse rounded-lg" />
                ))}
              </div>
            ) : upcomingSessions.length === 0 ? (
              <div className="py-8 text-center flex flex-col items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-bg-alt flex items-center justify-center text-text-secondary border border-border">
                  <Calendar size={18} />
                </div>
                <div className="text-left text-center">
                  <p className="font-semibold text-sm">No upcoming sessions</p>
                  <p className="text-xs text-text-secondary mt-0.5">
                    Schedule a mentoring class with one of our peer experts.
                  </p>
                </div>
                <Button size="sm" variant="outline" onClick={() => navigate("/mentors")} className="mt-2">
                  Browse Mentors
                </Button>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {upcomingSessions.map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-3.5 bg-bg border border-border rounded-lg"
                  >
                    <div className="flex items-center gap-3 text-left">
                      <div className="w-8 h-8 rounded-full bg-accent/10 text-accent flex items-center justify-center font-bold text-sm">
                        {session.mentor_name?.charAt(0) || "M"}
                      </div>
                      <div>
                        <p className="font-semibold text-sm">{session.skill_name || "Mentoring Session"}</p>
                        <p className="text-xs text-text-secondary mt-0.5">
                          with {session.mentor_name} • {new Date(session.scheduled_at).toLocaleDateString()} at {new Date(session.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                    <a
                      href={session.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 text-xs font-semibold bg-accent/10 text-accent hover:bg-accent/20 rounded-md transition-colors"
                    >
                      Join Call
                    </a>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* User Skills Summary Widget */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Skills You Offer" subtitle="What you can teach others">
              {isSkillsLoading ? (
                <div className="h-20 bg-border/40 animate-pulse rounded-lg" />
              ) : teachSkills.length === 0 ? (
                <p className="text-xs text-text-secondary italic">No teaching skills selected yet. Add some in profile settings!</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {teachSkills.map((s) => (
                    <span
                      key={s.id}
                      className="px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-600 rounded-full border border-green-500/10"
                    >
                      {s.skill?.name || s.name}
                    </span>
                  ))}
                </div>
              )}
            </Card>
            <Card title="Skills You Seek" subtitle="What you want to learn">
              {isSkillsLoading ? (
                <div className="h-20 bg-border/40 animate-pulse rounded-lg" />
              ) : learnSkills.length === 0 ? (
                <p className="text-xs text-text-secondary italic">No learning goals configured. Generate an AI Roadmap to start!</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {learnSkills.map((s) => (
                    <span
                      key={s.id}
                      className="px-2.5 py-1 text-xs font-medium bg-accent/10 text-accent rounded-full border border-accent/10"
                    >
                      {s.skill?.name || s.name}
                    </span>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>

        {/* Right Column (Wallet & AI Quick Actions) */}
        <div className="flex flex-col gap-6">
          {/* Wallet Balance Widget */}
          <Card title="Wallet Balance" subtitle="Swap Skill Coins to schedule lessons">
            {isWalletLoading ? (
              <div className="h-16 bg-border/40 animate-pulse rounded-lg" />
            ) : (
              <div className="flex items-center justify-between p-4 bg-bg border border-border rounded-lg text-left">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-yellow-500/10 text-yellow-500">
                    <WalletIcon size={20} />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-bold text-text-secondary tracking-wider">
                      Current Balance
                    </p>
                    <p className="text-2xl font-bold text-text mt-0.5">
                      {wallet?.balance ?? "—"} <span className="text-xs font-semibold text-text-secondary">Coins</span>
                    </p>
                  </div>
                </div>
                <Button size="sm" variant="ghost" onClick={() => navigate("/wallet")} className="px-1.5">
                  <ChevronRight size={18} />
                </Button>
              </div>
            )}
            <p className="text-[11px] text-text-secondary mt-3 text-left">
              Earn 5 coins for teaching a class. Spend 5 coins to book a lesson with any peer mentor.
            </p>
          </Card>

          {/* AI Features Hub (Quick Actions) */}
          <Card
            title="AI Learning Core"
            subtitle="Generate roadmaps & analyze gaps"
            className="border-accent/20 bg-accent/[0.01]"
          >
            <div className="flex flex-col gap-3 text-left">
              <button
                type="button"
                onClick={() => navigate("/journey/roadmap")}
                className="flex items-start gap-3 p-3 rounded-lg border border-border bg-bg hover:border-accent/40 cursor-pointer transition-all hover:-translate-y-0.5"
              >
                <div className="p-2 bg-accent/10 text-accent rounded-lg">
                  <Sparkles size={16} />
                </div>
                <div>
                  <h4 className="font-semibold text-xs text-text flex items-center gap-1">
                    AI Roadmap Builder <ArrowRight size={10} />
                  </h4>
                  <p className="text-[10px] text-text-secondary mt-0.5">
                    Generate a week-by-week visual curriculum for any topic.
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => navigate("/journey/skill-gap")}
                className="flex items-start gap-3 p-3 rounded-lg border border-border bg-bg hover:border-accent/40 cursor-pointer transition-all hover:-translate-y-0.5"
              >
                <div className="p-2 bg-accent/10 text-accent rounded-lg">
                  <BookOpen size={16} />
                </div>
                <div>
                  <h4 className="font-semibold text-xs text-text flex items-center gap-1">
                    Skill Gap Analyzer <ArrowRight size={10} />
                  </h4>
                  <p className="text-[10px] text-text-secondary mt-0.5">
                    Enter your target job role and see what skills you are missing.
                  </p>
                </div>
              </button>
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}
