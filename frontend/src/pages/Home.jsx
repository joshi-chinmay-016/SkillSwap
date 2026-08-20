import React, { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import api from "../services/api";
import { useAuthStore } from "../store/authStore";

// React Bits & 3D Visualizer Components
import KnowledgeEcosystem3D from "../components/webgl/KnowledgeEcosystem3D";
import LivePeerSwapSimulator from "../components/landing/LivePeerSwapSimulator";
import InteractiveAIMentorTerminal from "../components/landing/InteractiveAIMentorTerminal";
import LearningJourneyStory from "../components/landing/LearningJourneyStory";
import InfiniteMarquee from "../components/react-bits/InfiniteMarquee";
import PinnedCard, { PushPin } from "../components/common/PinnedCard";
import { MarkerHighlight, HandDrawnNote, SquigglyUnderline } from "../components/common/HandwrittenAnnotation";

// UI Primitives
import Button from "../components/common/Button";
import Footer from "../components/common/Footer";
import Avatar from "../components/common/Avatar";

// Icons
import {
  Sparkles,
  Users,
  Calendar,
  Target,
  ArrowRight,
  CheckCircle,
  BookOpen,
  Brain,
  Zap,
  ShieldCheck,
  Award,
  ArrowLeftRight,
  Flame,
  Search,
  MessageSquare,
  TrendingUp,
  FileText,
  Clock,
  Compass,
  Star,
  Cpu,
  Layers,
  Code2,
  Terminal,
  Bookmark,
  Pin,
} from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

const MARQUEE_SKILLS_ROW1 = [
  { name: "Python & FastAPI", icon: Code2, color: "text-emerald-600 dark:text-emerald-400", badge: "Backend" },
  { name: "React 19 & Next.js 15", icon: Zap, color: "text-sky-600 dark:text-sky-400", badge: "Frontend" },
  { name: "System Design & Arch", icon: Layers, color: "text-amber-600 dark:text-amber-400", badge: "Core" },
  { name: "PyTorch & AI Models", icon: Brain, color: "text-purple-600 dark:text-purple-400", badge: "AI" },
  { name: "UI / UX & Motion Design", icon: Sparkles, color: "text-rose-600 dark:text-rose-400", badge: "Design" },
  { name: "Docker & Kubernetes", icon: Cpu, color: "text-blue-600 dark:text-blue-400", badge: "DevOps" },
];

const MARQUEE_SKILLS_ROW2 = [
  { name: "PostgreSQL Indexing", icon: Terminal, color: "text-indigo-600 dark:text-indigo-400", badge: "Database" },
  { name: "LangChain & Vector RAG", icon: Brain, color: "text-purple-600 dark:text-purple-400", badge: "AI" },
  { name: "Tailwind CSS & Animations", icon: Sparkles, color: "text-cyan-600 dark:text-cyan-400", badge: "UI" },
  { name: "TypeScript Microservices", icon: Code2, color: "text-blue-600 dark:text-blue-400", badge: "Backend" },
  { name: "GraphQL & WebSockets", icon: Zap, color: "text-pink-600 dark:text-pink-400", badge: "FullStack" },
];

export default function Home() {
  const user = useAuthStore((state) => state.user);
  const heroRef = useRef(null);
  const howItWorksRef = useRef(null);

  // Fetch real mentors from backend
  const { data: mentors = [] } = useQuery({
    queryKey: ["landingMentors"],
    queryFn: async () => {
      try {
        const res = await api.get("/mentors/", { params: { limit: 4 } });
        return Array.isArray(res.data) ? res.data.slice(0, 4) : [];
      } catch {
        return [];
      }
    },
    retry: false,
  });

  // GSAP timeline for Hero entrance
  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.from(".hero-badge", { opacity: 0, y: -15, duration: 0.5, delay: 0.1 })
        .from(".hero-headline", { opacity: 0, y: 25, duration: 0.7 }, "-=0.3")
        .from(".hero-subtitle", { opacity: 0, y: 20, duration: 0.6 }, "-=0.4")
        .from(".hero-cta-group", { opacity: 0, y: 20, duration: 0.5 }, "-=0.3")
        .from(".hero-webgl-container", { opacity: 0, scale: 0.94, duration: 0.8 }, "-=0.4");
    }, heroRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={heroRef} className="min-h-screen whiteboard-grid text-text transition-colors duration-200 selection:bg-yellow-200 selection:text-slate-900 overflow-x-hidden">
      {/* Top Classroom Header */}
      <nav className="sticky top-0 z-50 glass-panel border-b border-border/80 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-18">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center text-white shadow-md group-hover:rotate-6 transition-transform duration-200">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                  />
                </svg>
              </div>
              <span className="font-black text-xl tracking-tight text-text">
                Skill<span className="text-accent">Swap</span>{" "}
                <span className="font-handwriting text-lg font-bold text-rose-500 rotate-[-4deg] inline-block ml-1">
                  Arena 📌
                </span>
              </span>
            </Link>

            {/* Nav Center Links */}
            <div className="hidden md:flex items-center gap-6 text-xs font-bold text-text-secondary">
              <a href="#simulator" className="hover:text-accent transition-colors">Matchmaker</a>
              <a href="#whiteboard-steps" className="hover:text-accent transition-colors">How It Works</a>
              <a href="#terminal" className="hover:text-accent transition-colors">AI Mentor</a>
              <a href="#journey" className="hover:text-accent transition-colors">Roadmap</a>
              <a href="#pinned-mentors" className="hover:text-accent transition-colors">Peer Mentors</a>
            </div>

            {/* Nav Actions */}
            <div className="flex items-center gap-3">
              {user ? (
                <Link to="/dashboard">
                  <Button variant="primary" size="sm" rightIcon={ArrowRight} className="shadow-glow">
                    Command Center
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" size="sm">
                      Sign In
                    </Button>
                  </Link>
                  <Link to="/register">
                    <Button variant="primary" size="sm" rightIcon={ArrowRight} className="shadow-glow">
                      Join Classroom Free
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* =========================================================================
          SECTION 1 — HERO WITH 3D PINNED WHITEBOARD & CAVEAT SCRIPT
      ========================================================================= */}
      <section className="relative overflow-hidden pt-10 pb-16 md:pt-14 md:pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-6 items-center">
            {/* Left Content */}
            <div className="lg:col-span-6 space-y-6 text-left">
              {/* Classroom Sticky Badge */}
              <div className="hero-badge inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-yellow-100 dark:bg-yellow-950/80 border border-yellow-300 dark:border-yellow-700 text-amber-900 dark:text-amber-300 text-xs font-bold shadow-xs">
                <span className="text-rose-500 font-handwriting text-base font-bold rotate-[-3deg]">📌 Class is in Session</span>
                <span className="text-text-muted">•</span>
                <span className="font-semibold">Peer-to-Peer Knowledge Board</span>
              </div>

              {/* Main Headline with Hand-Drawn Caveat & Marker Highlighting */}
              <div className="space-y-1">
                <h1 className="hero-headline text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-text leading-[1.15]">
                  Learn from peers. <br />
                  <MarkerHighlight color="yellow">Teach what you know.</MarkerHighlight>
                </h1>
                <div className="pt-2 flex items-center gap-3">
                  <HandDrawnNote color="rose" rotate="-2deg">
                    ✦ Zero fees. 100% Student Swaps!
                  </HandDrawnNote>
                  <SquigglyUnderline className="text-rose-500 max-w-[180px]" />
                </div>
              </div>

              <p className="hero-subtitle text-base sm:text-lg text-text-secondary max-w-xl leading-relaxed">
                Connect directly with verified student mentors to exchange skills in 1-on-1 sessions. Pinned to a collective knowledge board, powered by Skill Coins and a grounded AI mentor.
              </p>

              <div className="hero-cta-group flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5 pt-2">
                <Link to={user ? "/dashboard" : "/register"}>
                  <Button variant="primary" size="lg" className="w-full sm:w-auto shadow-glow font-bold" rightIcon={ArrowRight}>
                    {user ? "Open Classroom Center" : "Claim Your Free Spot"}
                  </Button>
                </Link>
                <a href="#simulator">
                  <Button variant="secondary" size="lg" className="w-full sm:w-auto">
                    Try Match Simulator
                  </Button>
                </a>
              </div>

              {/* Whiteboard Sticky Notes Row */}
              <div className="pt-4 grid grid-cols-3 gap-3 border-t border-border/80">
                <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-left rotate-[-1deg]">
                  <span className="font-handwriting text-base font-bold text-amber-800 dark:text-amber-300 block">📌 Peer Verified</span>
                  <span className="text-[11px] text-text-secondary font-medium">10-Question Tests</span>
                </div>
                <div className="p-3 rounded-xl bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800 text-left rotate-[1.5deg]">
                  <span className="font-handwriting text-base font-bold text-sky-800 dark:text-sky-300 block">⚡ Skill Coins</span>
                  <span className="text-[11px] text-text-secondary font-medium">Zero Cash Required</span>
                </div>
                <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-left rotate-[-1.5deg]">
                  <span className="font-handwriting text-base font-bold text-purple-800 dark:text-purple-300 block">🤖 Grounded AI</span>
                  <span className="text-[11px] text-text-secondary font-medium">Vector RAG Citations</span>
                </div>
              </div>
            </div>

            {/* Right 3D Pinned Whiteboard Scene */}
            <div className="hero-webgl-container lg:col-span-6 relative flex items-center justify-center">
              <KnowledgeEcosystem3D />
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          CONTINUOUS INFINITE SKILL RIBBONS (WHITEBOARD MARKER STYLE)
      ========================================================================= */}
      <section className="py-5 bg-surface-elevated/70 border-y border-border/80 space-y-3">
        <InfiniteMarquee items={MARQUEE_SKILLS_ROW1} speed={25} />
        <InfiniteMarquee items={MARQUEE_SKILLS_ROW2} reverse={true} speed={28} />
      </section>

      {/* =========================================================================
          SECTION 2 — LIVE PEER SWAP MATCHMAKER SIMULATOR
      ========================================================================= */}
      <section id="simulator" className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <LivePeerSwapSimulator />
        </div>
      </section>

      {/* =========================================================================
          SECTION 3 — PINNED CORKBOARD CARDS (HOW SKILLSWAP WORKS)
      ========================================================================= */}
      <section id="whiteboard-steps" ref={howItWorksRef} className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-yellow-100 dark:bg-yellow-950 border border-yellow-300 dark:border-yellow-700 text-amber-900 dark:text-amber-300 text-xs font-bold uppercase tracking-wider">
              <span className="font-handwriting text-base font-bold text-rose-500">📌 The Classroom Board</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-text">
              How SkillSwap Works
            </h2>
            <p className="text-sm sm:text-base text-text-secondary">
              Four steps pinned on our collective blackboard. Move from learner to verified peer mentor.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-7">
            {[
              {
                step: "01",
                title: "Pin Your Offerings",
                description: "Post what skills you can teach to peers and mark target topics you want to learn.",
                icon: Pin,
                pinColor: "red",
                sway: "left",
                note: "Step 1 📌",
                markerHighlight: "highlight-marker-yellow",
              },
              {
                step: "02",
                title: "Find Peer Matches",
                description: "Our algorithmic matchmaker pairs you with classmates who possess your target knowledge.",
                icon: Users,
                pinColor: "cyan",
                sway: "right",
                note: "Match! 🤝",
                markerHighlight: "highlight-marker-cyan",
              },
              {
                step: "03",
                title: "Live Whiteboard Call",
                description: "Meet in real-time 1-on-1 video rooms with shared notes, live code, and design reviews.",
                icon: Calendar,
                pinColor: "yellow",
                sway: "left",
                note: "1-on-1 ⚡",
                markerHighlight: "highlight-marker-emerald",
              },
              {
                step: "04",
                title: "Earn Coins & Badges",
                description: "Complete evaluations to verify skills and collect Skill Coins to fund your next study session.",
                icon: Award,
                pinColor: "purple",
                sway: "right",
                note: "Level Up! 🏆",
                markerHighlight: "highlight-marker-pink",
              },
            ].map((step) => {
              const Icon = step.icon;
              return (
                <PinnedCard
                  key={step.step}
                  pinColor={step.pinColor}
                  sway={step.sway}
                  note={step.note}
                  className="h-full flex flex-col justify-between"
                >
                  <div className="space-y-4 pt-1">
                    <div className="flex items-center justify-between">
                      <span className="text-3xl font-black text-accent/30 font-heading">{step.step}</span>
                      <span className="font-handwriting text-base font-bold text-text-secondary">
                        Lesson {step.step}
                      </span>
                    </div>

                    <div className="w-12 h-12 rounded-2xl bg-surface-elevated border border-border flex items-center justify-center text-accent shadow-xs">
                      <Icon size={22} />
                    </div>

                    <h3 className="text-lg font-bold text-text tracking-tight">
                      {step.title}
                    </h3>

                    <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </PinnedCard>
              );
            })}
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 4 — INTERACTIVE AI GROUNDED RAG TERMINAL
      ========================================================================= */}
      <section id="terminal" className="py-24 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-950 border border-purple-300 dark:border-purple-800 text-purple-900 dark:text-purple-300 text-xs font-bold uppercase tracking-wider">
              <Brain size={14} />
              <span>Grounded Textbook Assistant</span>
            </div>
            <h3 className="text-3xl sm:text-4xl font-black tracking-tight text-text">
              AI Mentor Grounded in <MarkerHighlight color="cyan">Real Courseware</MarkerHighlight>
            </h3>
            <p className="text-xs sm:text-sm text-text-secondary">
              Test queries below to inspect real-time vector citations and zero-hallucination document synthesis.
            </p>
          </div>

          <InteractiveAIMentorTerminal />
        </div>
      </section>

      {/* =========================================================================
          SECTION 5 — LEARNING JOURNEY PROGRESSION PIPELINE
      ========================================================================= */}
      <section id="journey" className="py-20 relative border-t border-border/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14 space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950 border border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-300 text-xs font-bold uppercase tracking-wider">
              <Compass size={13} />
              <span>Step-by-Step Curriculum</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-text">
              The Peer Learning Syllabus
            </h2>
            <p className="text-xs sm:text-sm text-text-secondary">
              From identifying skill gaps to 1-on-1 sessions and mastering high-demand engineering skills.
            </p>
          </div>

          <LearningJourneyStory />
        </div>
      </section>

      {/* =========================================================================
          SECTION 6 — PINNED MENTOR CARDS (REAL DATA)
      ========================================================================= */}
      <section id="pinned-mentors" className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-950 border border-yellow-300 dark:border-yellow-700 text-amber-900 dark:text-amber-300 text-xs font-semibold uppercase tracking-wider mb-2">
                <Users size={13} />
                <span>Classroom Peer Directory</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-text">
                Pinned Peer Mentors
              </h2>
              <p className="text-xs sm:text-sm text-text-secondary mt-1 max-w-xl">
                Browse student mentors pinned to our active directory ready for live 1-on-1 sessions.
              </p>
            </div>

            <Link to="/mentors">
              <Button variant="secondary" size="md" rightIcon={ArrowRight}>
                View All Mentors 📌
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-7">
            {mentors.length > 0 ? (
              mentors.map((mentor, index) => {
                const pinColors = ["red", "cyan", "yellow", "purple"];
                const sway = index % 2 === 0 ? "left" : "right";
                return (
                  <PinnedCard
                    key={mentor.id}
                    pinColor={pinColors[index % pinColors.length]}
                    sway={sway}
                    note={`⭐ ${mentor.rating ? Number(mentor.rating).toFixed(1) : "5.0"}`}
                    onClick={() => (window.location.href = `/mentors/${mentor.id}`)}
                    className="h-full flex flex-col justify-between"
                  >
                    <div className="space-y-3 pt-1">
                      <div className="flex items-center gap-3">
                        <Avatar src={mentor.avatar_url} alt={mentor.name} size="md" />
                        <div className="min-w-0 flex-1">
                          <h4 className="font-bold text-text text-sm truncate">{mentor.name}</h4>
                          <span className="text-[11px] text-text-secondary truncate block font-handwriting text-sm">
                            {mentor.headline || "Verified Peer Mentor"}
                          </span>
                        </div>
                      </div>

                      <div className="pt-2 border-t border-border/60 space-y-1.5 text-xs">
                        <span className="text-[10px] text-text-muted font-bold uppercase">Teaching Offering:</span>
                        <div className="flex flex-wrap gap-1">
                          {(mentor.skills || []).slice(0, 3).map((s, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold text-[10px] border border-emerald-500/20">
                              {typeof s === "string" ? s : s.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs font-bold text-accent">
                      <span>Schedule Swap</span>
                      <ArrowRight size={13} />
                    </div>
                  </PinnedCard>
                );
              })
            ) : (
              [
                { role: "Backend Engineering", teaches: ["FastAPI", "PostgreSQL", "Docker"], pinColor: "red", sway: "left" },
                { role: "Frontend UI/UX", teaches: ["React 19", "Tailwind CSS", "Figma"], pinColor: "cyan", sway: "right" },
                { role: "Machine Learning", teaches: ["PyTorch", "LangChain", "Vector RAG"], pinColor: "yellow", sway: "left" },
                { role: "Cloud & DevOps", teaches: ["Kubernetes", "AWS", "CI/CD"], pinColor: "purple", sway: "right" },
              ].map((item, idx) => (
                <PinnedCard
                  key={idx}
                  pinColor={item.pinColor}
                  sway={item.sway}
                  note={`Class #${idx + 1}`}
                  className="h-full flex flex-col justify-between"
                >
                  <div className="space-y-3 pt-1">
                    <div className="w-10 h-10 rounded-2xl bg-accent/10 text-accent flex items-center justify-center font-black text-sm">
                      0{idx + 1}
                    </div>
                    <div>
                      <h4 className="font-bold text-text text-sm">{item.role}</h4>
                      <p className="text-xs text-text-secondary font-handwriting mt-0.5">Ready for 1-on-1 swaps</p>
                    </div>

                    <div className="pt-2 border-t border-border/60 space-y-1 text-xs">
                      <span className="text-[10px] text-text-muted font-bold uppercase">Teaches:</span>
                      <div className="flex flex-wrap gap-1">
                        {item.teaches.map((t, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-500/20">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <Link to="/register" className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs text-accent font-bold hover:underline">
                    <span>Match with Peer</span>
                    <ArrowRight size={13} />
                  </Link>
                </PinnedCard>
              ))
            )}
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 7 — FINAL CLASSROOM CTA
      ========================================================================= */}
      <section className="py-24 relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <PinnedCard pinColor="red" tape={true} className="p-10 sm:p-16 border-2 border-accent/40 shadow-2xl">
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="space-y-2">
                <span className="font-handwriting text-2xl font-bold text-rose-500 rotate-[-2deg] inline-block">
                  ✦ Final Call for Study Sessions!
                </span>
                <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-text leading-tight">
                  Your next skill is <MarkerHighlight color="yellow">one conversation away.</MarkerHighlight>
                </h2>
              </div>
              <p className="text-sm sm:text-base text-text-secondary">
                Join our peer learning classroom today. Teach what you love, learn what you need, and master engineering with zero monetary cost.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                <Link to={user ? "/dashboard" : "/register"}>
                  <Button variant="primary" size="lg" className="w-full sm:w-auto shadow-glow font-bold" rightIcon={ArrowRight}>
                    {user ? "Go to Dashboard" : "Claim Your Free Desk"}
                  </Button>
                </Link>
                <Link to="/mentors">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    Browse All Mentors
                  </Button>
                </Link>
              </div>
            </div>
          </PinnedCard>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}