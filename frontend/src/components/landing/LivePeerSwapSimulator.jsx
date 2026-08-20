import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ArrowLeftRight,
  Code,
  Zap,
  Sparkles,
  CheckCircle2,
  UserCheck,
  Video,
  Clock,
  Play,
  RotateCcw,
  Coins,
  Flame,
} from "lucide-react";
import Button from "../common/Button";
import Card3DTilt from "../react-bits/Card3DTilt";
import ShinyText from "../react-bits/ShinyText";

const TEACH_SKILLS = [
  { id: "fastapi", name: "FastAPI Backend", category: "Backend", color: "from-emerald-500 to-teal-600" },
  { id: "react", name: "React & Next.js", category: "Frontend", color: "from-cyan-500 to-blue-600" },
  { id: "pytorch", name: "PyTorch & AI", category: "Machine Learning", color: "from-purple-500 to-indigo-600" },
  { id: "uiux", name: "UI / UX Design", category: "Design", color: "from-pink-500 to-rose-600" },
  { id: "sysdesign", name: "System Design", category: "Architecture", color: "from-amber-500 to-orange-600" },
];

const LEARN_SKILLS = [
  { id: "sysdesign", name: "System Design", category: "Architecture", matchScore: 98 },
  { id: "uiux", name: "UI / UX Design", category: "Design", matchScore: 95 },
  { id: "fastapi", name: "FastAPI Backend", category: "Backend", matchScore: 94 },
  { id: "pytorch", name: "PyTorch & AI", category: "Machine Learning", matchScore: 99 },
  { id: "react", name: "React & Next.js", category: "Frontend", matchScore: 96 },
];

export default function LivePeerSwapSimulator() {
  const [selectedTeach, setSelectedTeach] = useState(TEACH_SKILLS[0]);
  const [selectedLearn, setSelectedLearn] = useState(LEARN_SKILLS[1]);
  const [isSwapping, setIsSwapping] = useState(false);
  const [swapCompleted, setSwapCompleted] = useState(false);

  const calculateCompatibility = () => {
    if (selectedTeach.id === selectedLearn.id) return 92;
    return Math.min(99, 88 + ((selectedTeach.name.length + selectedLearn.name.length) % 11));
  };

  const score = calculateCompatibility();

  const handleSimulateSwap = () => {
    setIsSwapping(true);
    setSwapCompleted(false);
    setTimeout(() => {
      setIsSwapping(false);
      setSwapCompleted(true);
    }, 1600);
  };

  return (
    <div className="w-full max-w-5xl mx-auto rounded-3xl border border-card-border bg-card-bg/95 backdrop-blur-2xl p-6 sm:p-10 shadow-2xl relative overflow-hidden text-left">
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-accent/10 rounded-full blur-3xl opacity-70" />

      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-accent/10 border border-accent/25 text-accent text-xs font-black uppercase tracking-wider">
          <Sparkles size={14} className="animate-spin-slow" />
          <span>Interactive Peer Matchmaker</span>
        </div>
        <h3 className="text-2xl sm:text-4xl font-black tracking-tight text-text">
          Experience Live <ShinyText text="Knowledge Exchange" />
        </h3>
        <p className="text-xs sm:text-sm text-text-secondary">
          Pick what you can teach and what you want to learn. Watch our algorithm calculate instant peer compatibility!
        </p>
      </div>

      {/* Interactive Selectors Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Teach Selector */}
        <div className="p-4 sm:p-5 rounded-2xl bg-surface-elevated border border-border/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              1. Choose What You Teach
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
              Your Offering
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {TEACH_SKILLS.map((skill) => (
              <button
                key={skill.id}
                onClick={() => {
                  setSelectedTeach(skill);
                  setSwapCompleted(false);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all duration-150 cursor-pointer ${
                  selectedTeach.id === skill.id
                    ? "bg-emerald-600 text-white shadow-md scale-105"
                    : "bg-bg-alt text-text-secondary hover:text-text border border-border"
                }`}
              >
                {skill.name}
              </button>
            ))}
          </div>
        </div>

        {/* Learn Selector */}
        <div className="p-4 sm:p-5 rounded-2xl bg-surface-elevated border border-border/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-accent uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-accent" />
              2. Choose What You Learn
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-accent/10 text-accent">
              Target Goal
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {LEARN_SKILLS.map((skill) => (
              <button
                key={skill.id}
                onClick={() => {
                  setSelectedLearn(skill);
                  setSwapCompleted(false);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all duration-150 cursor-pointer ${
                  selectedLearn.id === skill.id
                    ? "bg-accent text-white shadow-md scale-105"
                    : "bg-bg-alt text-text-secondary hover:text-text border border-border"
                }`}
              >
                {skill.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3D Bilateral Match Visualizer Canvas */}
      <div className="grid grid-cols-1 md:grid-cols-7 gap-4 items-center mb-8">
        {/* Peer A 3D Tilt Card */}
        <div className="md:col-span-3">
          <Card3DTilt className="p-5 sm:p-6 space-y-4">
            <div className="flex items-center gap-3.5">
              <div className={`w-12 h-12 rounded-2xl bg-gradient-to-tr ${selectedTeach.color} flex items-center justify-center text-white font-black text-xl shadow-md`}>
                U
              </div>
              <div>
                <h4 className="font-extrabold text-sm text-text">You (Peer Mentor)</h4>
                <span className="inline-flex items-center gap-1 text-[11px] text-emerald-500 font-semibold">
                  <UserCheck size={12} /> Verified Member
                </span>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-border/80 text-xs">
              <div>
                <span className="text-text-muted text-[10px] uppercase font-bold block mb-1">Teaches (Offering):</span>
                <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold inline-block border border-emerald-500/20">
                  {selectedTeach.name}
                </span>
              </div>
              <div>
                <span className="text-text-muted text-[10px] uppercase font-bold block mb-1">Seeking Mastery In:</span>
                <span className="px-2.5 py-1 rounded-lg bg-accent/10 text-accent font-bold inline-block border border-accent/20">
                  {selectedLearn.name}
                </span>
              </div>
            </div>
          </Card3DTilt>
        </div>

        {/* Center Connection Node */}
        <div className="md:col-span-1 flex flex-col items-center justify-center text-center py-2">
          <motion.div
            animate={isSwapping ? { rotate: 360, scale: [1, 1.25, 1] } : { rotate: 0 }}
            transition={{ duration: 1.2, repeat: isSwapping ? Infinity : 0, ease: "linear" }}
            className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-accent to-purple-600 p-[2px] shadow-glow"
          >
            <div className="w-full h-full bg-bg rounded-[14px] flex items-center justify-center">
              <ArrowLeftRight className="text-accent" size={22} />
            </div>
          </motion.div>

          <span className="text-[10px] font-black text-accent mt-2 px-2 py-0.5 rounded-full bg-accent/10 border border-accent/20">
            {score}% Match
          </span>
        </div>

        {/* Peer B 3D Tilt Card */}
        <div className="md:col-span-3">
          <Card3DTilt className="p-5 sm:p-6 space-y-4">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-pink-500 to-indigo-600 flex items-center justify-center text-white font-black text-xl shadow-md">
                P
              </div>
              <div>
                <h4 className="font-extrabold text-sm text-text">Compatible Peer Match</h4>
                <span className="inline-flex items-center gap-1 text-[11px] text-accent font-semibold">
                  <Flame size={12} className="text-amber-500" /> High Activity
                </span>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-border/80 text-xs">
              <div>
                <span className="text-text-muted text-[10px] uppercase font-bold block mb-1">Teaches (Offering):</span>
                <span className="px-2.5 py-1 rounded-lg bg-pink-500/10 text-pink-600 dark:text-pink-400 font-bold inline-block border border-pink-500/20">
                  {selectedLearn.name}
                </span>
              </div>
              <div>
                <span className="text-text-muted text-[10px] uppercase font-bold block mb-1">Wants to Learn:</span>
                <span className="px-2.5 py-1 rounded-lg bg-accent/10 text-accent font-bold inline-block border border-accent/20">
                  {selectedTeach.name}
                </span>
              </div>
            </div>
          </Card3DTilt>
        </div>
      </div>

      {/* Simulation Action Bar */}
      <div className="p-4 sm:p-5 rounded-2xl bg-accent/5 border border-accent/20 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 text-xs">
          <div className="p-2 rounded-xl bg-accent/10 text-accent">
            <Coins size={18} />
          </div>
          <div>
            <span className="font-bold text-text">Economic Balance:</span>{" "}
            <span className="text-text-secondary">
              You teach {selectedTeach.name} (+5 Coins) • You learn {selectedLearn.name} (-5 Coins) = <strong>0 Net Cost</strong>
            </span>
          </div>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={handleSimulateSwap}
          isLoading={isSwapping}
          rightIcon={isSwapping ? null : Play}
          className="w-full sm:w-auto shadow-glow font-bold"
        >
          {isSwapping ? "Simulating Live Swap..." : "Simulate Live 1-on-1 Swap"}
        </Button>
      </div>

      {/* Success Celebration Simulation Dialog */}
      <AnimatePresence>
        {swapCompleted && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="mt-6 p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg"
          >
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-glow">
                <CheckCircle2 size={22} />
              </div>
              <div className="space-y-0.5">
                <h4 className="font-extrabold text-sm text-text">
                  Bilateral Peer Session Initialized! 🎉
                </h4>
                <p className="text-xs text-text-secondary">
                  Ready to connect on <strong>{selectedTeach.name} ↔ {selectedLearn.name}</strong>. Join the real platform to schedule your session today.
                </p>
              </div>
            </div>

            <Button
              size="sm"
              variant="primary"
              onClick={() => (window.location.href = "/register")}
              className="shrink-0 font-black bg-emerald-600 hover:bg-emerald-500 text-white shadow-glow px-5 py-2.5 cursor-pointer"
            >
              Claim Your Free Spot →
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
