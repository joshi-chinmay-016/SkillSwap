import React from "react";
import { motion, useReducedMotion } from "motion/react";
import { HelpCircle, Database, Layers, Sparkles } from "lucide-react";

export default function KnowledgePipelineVisual() {
  const shouldReduceMotion = useReducedMotion();

  const steps = [
    { icon: HelpCircle, label: "User Question", color: "text-accent", bg: "bg-accent/10 border-accent/20" },
    { icon: Database, label: "FAISS Vector Space", color: "text-primary", bg: "bg-primary/10 border-primary/20" },
    { icon: Layers, label: "Bounded Context", color: "text-warning", bg: "bg-warning/10 border-warning/20" },
    { icon: Sparkles, label: "Grounded Answer", color: "text-success", bg: "bg-success/10 border-success/20" },
  ];

  return (
    <div className="w-full py-4 px-6 bg-bg-alt/40 border border-border rounded-2xl mb-6 shadow-sm overflow-hidden">
      <div className="text-[11px] font-bold text-text-secondary uppercase tracking-wider mb-3">
        RAG Architectural Knowledge Pipeline
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 relative">
        {steps.map((step, idx) => {
          const IconComponent = step.icon;
          return (
            <motion.div
              key={step.label}
              initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="p-3 bg-bg border border-border rounded-xl flex items-center gap-3 relative z-10 shadow-sm"
              style={{
                transform: shouldReduceMotion ? "none" : `perspective(600px) translateZ(${10 - idx * 2}px)`,
              }}
            >
              <div className={`w-8 h-8 rounded-lg ${step.bg} border flex items-center justify-center ${step.color} shrink-0`}>
                <IconComponent size={16} />
              </div>
              <div className="min-w-0">
                <div className="text-[10px] font-semibold text-text-secondary uppercase">Stage {idx + 1}</div>
                <div className="text-xs font-bold text-text truncate">{step.label}</div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
