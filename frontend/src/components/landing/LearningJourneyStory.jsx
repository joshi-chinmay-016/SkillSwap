import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Target, Calendar, Code, MessageSquare, TrendingUp, Award, ChevronRight, CheckCircle2 } from "lucide-react";

export default function LearningJourneyStory() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      id: 0,
      title: "1. Select Target Skill",
      icon: Target,
      tag: "Skill Goal",
      description: "Define what you want to master. Analyze your skill gap against industry benchmarks.",
      visualBadge: "e.g. Next.js 15 App Router",
      accentColor: "from-blue-500 to-indigo-600",
    },
    {
      id: 1,
      title: "2. Live 1-on-1 Session",
      icon: Calendar,
      tag: "Peer Learning",
      description: "Book an interactive session with a verified student mentor who has hands-on experience.",
      visualBadge: "60 Min Code & Architecture Review",
      accentColor: "from-indigo-500 to-purple-600",
    },
    {
      id: 2,
      title: "3. Hands-on Practice",
      icon: Code,
      tag: "Real Projects",
      description: "Work on structured challenges, coding assignments, and personalized roadmap milestones.",
      visualBadge: "Build Production Full-Stack App",
      accentColor: "from-purple-500 to-pink-600",
    },
    {
      id: 3,
      title: "4. Actionable Feedback",
      icon: MessageSquare,
      tag: "Code Review",
      description: "Receive qualitative feedback and ratings from your peer mentor to fix blindspots quickly.",
      visualBadge: "Peer & AI Grounded Review",
      accentColor: "from-pink-500 to-rose-600",
    },
    {
      id: 4,
      title: "5. Reputation & Badges",
      icon: TrendingUp,
      tag: "Growth",
      description: "Earn Skill Coins and unlock verified credibility badges that validate your proficiency.",
      visualBadge: "+50 XP • Level 3 Mentor",
      accentColor: "from-amber-500 to-emerald-600",
    },
    {
      id: 5,
      title: "6. Complete Mastery",
      icon: Award,
      tag: "Pay It Forward",
      description: "Transition from learner to mentor. Teach newly joined students to earn more coins.",
      visualBadge: "Top Rated Peer Mentor",
      accentColor: "from-emerald-500 to-teal-600",
    },
  ];

  const currentStep = steps[activeStep];
  const CurrentIcon = currentStep.icon;

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8">
      {/* Step Buttons Progression Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isSelected = activeStep === idx;
          const isPassed = activeStep > idx;

          return (
            <button
              key={step.id}
              onClick={() => setActiveStep(idx)}
              className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between gap-3 ${
                isSelected
                  ? "bg-accent text-white border-accent shadow-glow"
                  : isPassed
                  ? "bg-surface-elevated text-text border-accent/40"
                  : "bg-surface-elevated/50 text-text-secondary border-border hover:border-accent/30"
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                    isSelected
                      ? "bg-white/20 text-white"
                      : isPassed
                      ? "bg-emerald-500/10 text-emerald-500"
                      : "bg-accent/10 text-accent"
                  }`}
                >
                  <Icon size={16} />
                </div>
                {isPassed && <CheckCircle2 size={14} className="text-emerald-500" />}
              </div>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider opacity-80">
                  Step {idx + 1}
                </p>
                <h4 className="text-xs font-bold truncate mt-0.5">
                  {step.title.split(". ")[1]}
                </h4>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Step Showcase Card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeStep}
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -15 }}
          transition={{ duration: 0.25 }}
          className="rounded-3xl border border-card-border bg-card-bg/95 p-6 sm:p-10 shadow-xl backdrop-blur-md relative overflow-hidden"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
            <div className="md:col-span-2 space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-semibold">
                <CurrentIcon size={14} />
                <span>{currentStep.tag}</span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-text">
                {currentStep.title}
              </h3>

              <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
                {currentStep.description}
              </p>

              <div className="pt-2">
                <span className="inline-block px-3 py-1.5 rounded-xl bg-surface-elevated border border-border text-xs font-semibold text-text shadow-xs">
                  Outcome: <strong className="text-accent">{currentStep.visualBadge}</strong>
                </span>
              </div>
            </div>

            {/* Visual Icon Illustration */}
            <div className="flex items-center justify-center">
              <div className={`w-32 h-32 sm:w-40 sm:h-40 rounded-3xl bg-gradient-to-tr ${currentStep.accentColor} p-1 shadow-glow flex items-center justify-center`}>
                <div className="w-full h-full bg-bg rounded-[22px] flex items-center justify-center text-text">
                  <CurrentIcon size={56} className="text-accent animate-pulse-subtle" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
