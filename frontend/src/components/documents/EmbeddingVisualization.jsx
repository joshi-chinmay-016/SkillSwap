import React from "react";
import { motion } from "motion/react";
import { FileText, Scissors, Cpu, Binary, Database, ArrowRight, Sparkles } from "lucide-react";

export default function EmbeddingVisualization({ modelName = "text-embedding-004", dimension = 768 }) {
  const steps = [
    {
      id: "doc",
      title: "Document",
      subtitle: "Source Knowledge",
      icon: FileText,
      color: "from-blue-500 to-indigo-600",
    },
    {
      id: "chunk",
      title: "Semantic Chunk",
      subtitle: "Intelligent Segment",
      icon: Scissors,
      color: "from-indigo-500 to-purple-600",
    },
    {
      id: "model",
      title: "Embedding Model",
      subtitle: modelName,
      icon: Cpu,
      color: "from-purple-500 to-pink-600",
    },
    {
      id: "vector",
      title: "Vector Representation",
      subtitle: `[ 0.018, -0.231, 0.442, ... ] (${dimension}-dim)`,
      icon: Binary,
      color: "from-pink-500 to-emerald-600",
      isConceptual: true,
    },
    {
      id: "storage",
      title: "Vector Storage Boundary",
      subtitle: "Indexed for Retrieval",
      icon: Database,
      color: "from-emerald-500 to-teal-600",
    },
  ];

  return (
    <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white shadow-xl border border-indigo-500/20 relative overflow-hidden">
      {/* Subtle Background Particle Animation */}
      <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#6366f1_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none" />

      <div className="relative z-10 space-y-4">
        {/* Header Explanation */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-indigo-400" />
            <h3 className="text-sm font-black tracking-tight text-white">
              Embedding Transformation Pipeline
            </h3>
          </div>
          <span className="text-[10px] font-extrabold uppercase tracking-widest text-indigo-300 bg-indigo-900/60 px-2.5 py-1 rounded-full border border-indigo-500/30">
            Conceptual Visual Flow
          </span>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed font-medium max-w-3xl">
          Embeddings transform each knowledge chunk into a numerical vector representation that allows the system to later perform semantic retrieval.
        </p>

        {/* Visual Pipeline Flow */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <React.Fragment key={step.id}>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1, duration: 0.4 }}
                  className="p-3.5 rounded-xl bg-slate-900/80 backdrop-blur-md border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col justify-between relative group"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${step.color} flex items-center justify-center text-white shadow-sm`}>
                      <Icon size={14} />
                    </div>
                    <span className="text-xs font-black text-white truncate">
                      {step.title}
                    </span>
                  </div>

                  <span className={`text-[10px] font-mono leading-tight ${step.isConceptual ? "text-emerald-400 font-bold" : "text-slate-400"}`}>
                    {step.subtitle}
                  </span>

                  {step.isConceptual && (
                    <span className="mt-2 text-[9px] font-bold tracking-wider uppercase text-amber-400/90 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-500/30 self-start">
                      Conceptual Vector
                    </span>
                  )}
                </motion.div>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
