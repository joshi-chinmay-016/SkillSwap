import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Sparkles, Brain, Cpu, Zap, Compass, Target, X } from "lucide-react";
import Modal from "./Modal";

const DEFAULT_STAGES = {
  roadmap: [
    { title: "Analyzing Target Role Requirements", subtitle: "Parsing industry competency standards..." },
    { title: "Mapping Current Skill Foundations", subtitle: "Evaluating existing skills and experience level..." },
    { title: "Synthesizing Weekly Milestones", subtitle: "Structuring optimal progressive learning modules..." },
    { title: "Curating Practice Tasks & Resources", subtitle: "Assembling actionable projects and reference guides..." },
    { title: "Finalizing Your Custom Roadmap", subtitle: "Almost ready to launch your learning journey..." },
  ],
  "skill-gap": [
    { title: "Scanning Role Competency Benchmarks", subtitle: "Analyzing target career prerequisites..." },
    { title: "Evaluating Current Skill Inventory", subtitle: "Comparing your skills against required expertise..." },
    { title: "Detecting Critical Gap Areas", subtitle: "Pinpointing missing proficiencies and priorities..." },
    { title: "Computing Match & Confidence Scores", subtitle: "Structuring prioritized recommendations..." },
    { title: "Finalizing Skill Gap Report", subtitle: "Generating customized bridge path..." },
  ],
  "mentor-match": [
    { title: "Scanning Peer Mentor Network", subtitle: "Filtering mentors by skill expertise..." },
    { title: "Evaluating Teaching Reputations", subtitle: "Calculating credibility and verified badges..." },
    { title: "Checking Real-time Availability", subtitle: "Finding active mentors with open slots..." },
    { title: "Ranking Compatibility Scores", subtitle: "Sorting by semantic match relevance..." },
    { title: "Finalizing Mentor Matches", subtitle: "Preparing your mentor recommendations..." },
  ],
  default: [
    { title: "Connecting to AI Engine", subtitle: "Initializing neural computation..." },
    { title: "Processing Semantic Context", subtitle: "Analyzing knowledge base and profile..." },
    { title: "Generating Grounded Insights", subtitle: "Synthesizing personalized results..." },
    { title: "Polishing Output", subtitle: "Applying final formatting and checks..." },
  ],
};

export default function AILoadingScreen({
  isOpen = true,
  type = "default",
  title = "AI in Progress",
  customStages = null,
  onCancel = null,
  inline = false,
}) {
  const stages = customStages || DEFAULT_STAGES[type] || DEFAULT_STAGES.default;
  const [currentStageIdx, setCurrentStageIdx] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef(null);
  const stageIntervalRef = useRef(null);

  useEffect(() => {
    if (!isOpen) {
      setCurrentStageIdx(0);
      setElapsed(0);
      return;
    }

    const start = Date.now();
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);

    stageIntervalRef.current = setInterval(() => {
      setCurrentStageIdx((prev) => (prev + 1) % stages.length);
    }, 2800);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (stageIntervalRef.current) clearInterval(stageIntervalRef.current);
    };
  }, [isOpen, stages.length]);

  const currentStage = stages[currentStageIdx] || stages[0];

  const content = (
    <div className="flex flex-col items-center justify-center text-center p-6 sm:p-8 max-w-md mx-auto select-none">
      {/* Animated Orb & Orbital Rings */}
      <div className="relative w-36 h-36 flex items-center justify-center mb-6">
        {/* Outer Glow */}
        <div className="absolute inset-0 rounded-full bg-accent/20 blur-xl animate-pulse" />

        {/* Orbit Ring 1 */}
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-dashed border-accent/40"
          animate={{ rotate: 360 }}
          transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
        />

        {/* Orbit Ring 2 */}
        <motion.div
          className="absolute inset-2 rounded-full border border-purple-500/30"
          animate={{ rotate: -360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
        />

        {/* Orbiting Satellite Dot */}
        <motion.div
          className="absolute inset-0 flex items-start justify-center"
          animate={{ rotate: 360 }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        >
          <div className="w-3.5 h-3.5 rounded-full bg-accent shadow-[0_0_12px_rgba(99,102,241,0.8)] -mt-1.5" />
        </motion.div>

        {/* Second Orbiting Satellite Dot */}
        <motion.div
          className="absolute inset-0 flex items-end justify-center"
          animate={{ rotate: -360 }}
          transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
        >
          <div className="w-2.5 h-2.5 rounded-full bg-purple-400 shadow-[0_0_10px_rgba(192,132,252,0.8)] -mb-1" />
        </motion.div>

        {/* Central Core */}
        <motion.div
          className="relative w-20 h-20 rounded-2xl bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center shadow-glow shadow-accent/40"
          animate={{
            scale: [1, 1.06, 1],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          {type === "roadmap" ? (
            <Compass size={36} className="text-white animate-spin-slow" />
          ) : type === "skill-gap" ? (
            <Target size={36} className="text-white animate-pulse" />
          ) : (
            <Brain size={36} className="text-white" />
          )}
        </motion.div>
      </div>

      {/* Stage Title and Subtitle with Smooth Animated Switch */}
      <div className="h-20 flex flex-col items-center justify-center mb-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStageIdx}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
            className="space-y-1"
          >
            <h3 className="text-base font-extrabold text-text tracking-tight flex items-center justify-center gap-2">
              <Sparkles size={16} className="text-accent animate-pulse" />
              <span>{currentStage.title}</span>
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed font-medium max-w-xs">
              {currentStage.subtitle}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Multi-stage Progress Indicators */}
      <div className="flex items-center justify-center gap-1.5 w-full max-w-xs mb-4">
        {stages.map((_, idx) => (
          <div
            key={idx}
            className={`h-1.5 rounded-full flex-1 transition-all duration-500 ${
              idx === currentStageIdx
                ? "bg-accent shadow-xs shadow-accent"
                : idx < currentStageIdx
                ? "bg-accent/40"
                : "bg-border"
            }`}
          />
        ))}
      </div>

      {/* Elapsed Counter / Long Running Hint */}
      <div className="flex items-center gap-2 text-[11px] text-text-secondary font-mono">
        <Cpu size={12} className="text-accent" />
        <span>Processing ({elapsed}s)</span>
      </div>

      {elapsed >= 15 && (
        <p className="text-[11px] text-amber-500/90 font-medium mt-2 animate-pulse">
          Crafting in-depth AI response, thank you for your patience...
        </p>
      )}

      {/* Cancel Button */}
      {onCancel && elapsed >= 6 && (
        <motion.button
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          type="button"
          onClick={onCancel}
          className="mt-5 px-4 py-1.5 rounded-xl border border-border text-xs font-bold text-text-secondary hover:text-danger hover:border-danger/40 hover:bg-danger/5 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <X size={13} />
          <span>Cancel Generation</span>
        </motion.button>
      )}
    </div>
  );

  if (inline) {
    return isOpen ? (
      <div className="w-full rounded-2xl border border-border bg-bg-alt/50 backdrop-blur-xs my-4 shadow-sm">
        {content}
      </div>
    ) : null;
  }

  return (
    <Modal isOpen={isOpen} onClose={onCancel || (() => {})} title="" size="md">
      {content}
    </Modal>
  );
}
