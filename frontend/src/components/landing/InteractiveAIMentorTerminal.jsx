import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Brain,
  Sparkles,
  FileText,
  CheckCircle,
  Copy,
  Terminal,
  Code2,
  Database,
  Layers,
  ArrowRight,
} from "lucide-react";
import Button from "../common/Button";
import ShinyText from "../react-bits/ShinyText";

const PROMPTS = [
  {
    id: 1,
    title: "FastAPI Caching Architecture",
    query: "How do we implement low-latency caching for peer session match queries?",
    response:
      "For peer matchmaking queries, utilize a dual-layer caching strategy with Redis for the BM25 candidate index and an in-memory LRU cache for active mentor availability slots.",
    code: `// Multi-Tier Caching Pattern
@router.get("/mentors/match")
async def get_matches(user_id: int, redis: Redis = Depends(get_redis)):
    cache_key = f"mentor_matches:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached) # ⚡ 4ms response
    
    matches = await compute_hybrid_match(user_id)
    await redis.setex(cache_key, 300, json.dumps(matches))
    return matches`,
    source: "Distributed-Systems-Handbook.pdf (Page 88)",
    similarity: "98.4%",
    memory: "Learner specializes in Python / FastAPI backend systems",
  },
  {
    id: 2,
    title: "React 19 Server Actions",
    query: "What is the optimal way to handle optimistic updates in React 19?",
    response:
      "React 19 introduces useOptimistic to provide instant UI feedback before server mutation resolves, automatically rolling back on error.",
    code: `// React 19 Optimistic Booking
const [optimisticSessions, setOptimistic] = useOptimistic(
  sessions,
  (state, newSession) => [...state, { ...newSession, pending: true }]
);

async function handleBook(formData) {
  setOptimistic({ id: Date.now(), title: "Pending Session" });
  await bookSessionAction(formData);
}`,
    source: "React-19-Deep-Dive.pdf (Page 42)",
    similarity: "97.1%",
    memory: "Learner is currently preparing for Full-Stack Frontend certification",
  },
  {
    id: 3,
    title: "FAISS Vector RAG Pipeline",
    query: "How does SkillSwap chunk documents for grounded vector search?",
    response:
      "We use recursive character text splitting with 500-token chunks and 50-token overlap, embedded with all-MiniLM-L6-v2 into a FAISS FlatIP index.",
    code: `// RAG Ingestion Pipeline
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_text(raw_document)
embeddings = embedder.encode(chunks)
faiss_index.add(embeddings) # 🔍 Fast Cosine Indexing`,
    source: "Vector-RAG-Engineering.pdf (Page 15)",
    similarity: "99.2%",
    memory: "Document library contains 12 active engineering coursebooks",
  },
];

export default function InteractiveAIMentorTerminal() {
  const [selectedPrompt, setSelectedPrompt] = useState(PROMPTS[0]);
  const [activeInspectorTab, setActiveInspectorTab] = useState("answer"); // 'answer', 'source', 'memory'

  return (
    <div className="w-full max-w-5xl mx-auto rounded-3xl border border-card-border bg-card-bg/95 backdrop-blur-2xl shadow-2xl overflow-hidden text-left">
      {/* Terminal Window Top Bar */}
      <div className="px-6 py-4 bg-bg-alt/80 border-b border-border flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500/80" />
          <div className="w-3 h-3 rounded-full bg-amber-500/80" />
          <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          <span className="text-xs font-mono font-bold text-text-muted ml-2">
            SkillSwap AI Grounded RAG Terminal v2.4
          </span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-[10px] font-black">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Grounded in Real Documents</span>
        </div>
      </div>

      {/* Interactive Prompt Selection Buttons */}
      <div className="p-4 sm:p-6 bg-bg/50 border-b border-border/70">
        <span className="text-[10px] font-black uppercase tracking-wider text-text-muted block mb-2.5">
          Select A Simulated Query:
        </span>
        <div className="flex flex-wrap gap-2">
          {PROMPTS.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelectedPrompt(p)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all duration-150 cursor-pointer ${
                selectedPrompt.id === p.id
                  ? "bg-accent text-white shadow-glow"
                  : "bg-surface-elevated text-text-secondary hover:text-text border border-border"
              }`}
            >
              {p.title}
            </button>
          ))}
        </div>
      </div>

      {/* Terminal Body */}
      <div className="p-6 sm:p-8 space-y-6">
        {/* User Query Bubble */}
        <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-surface-elevated border border-border/80 text-xs text-text shadow-xs">
          <div className="w-7 h-7 rounded-lg bg-accent/15 text-accent flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
            Q
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-text-muted block">Student Prompt</span>
            <p className="font-semibold mt-0.5 text-text leading-relaxed">
              &ldquo;{selectedPrompt.query}&rdquo;
            </p>
          </div>
        </div>

        {/* AI Answer & Inspector Tabs */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-accent" />
              <span className="text-xs font-bold text-text">Synthesized Grounded Response</span>
            </div>

            <div className="flex items-center gap-1 p-1 bg-bg-alt rounded-xl border border-border text-[11px] font-semibold">
              <button
                onClick={() => setActiveInspectorTab("answer")}
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                  activeInspectorTab === "answer" ? "bg-accent text-white font-bold" : "text-text-secondary hover:text-text"
                }`}
              >
                Code & Explanation
              </button>
              <button
                onClick={() => setActiveInspectorTab("source")}
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                  activeInspectorTab === "source" ? "bg-accent text-white font-bold" : "text-text-secondary hover:text-text"
                }`}
              >
                RAG Citation
              </button>
              <button
                onClick={() => setActiveInspectorTab("memory")}
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                  activeInspectorTab === "memory" ? "bg-accent text-white font-bold" : "text-text-secondary hover:text-text"
                }`}
              >
                Mentor Memory
              </button>
            </div>
          </div>

          <AnimatePresence mode="wait">
            {activeInspectorTab === "answer" && (
              <motion.div
                key={`ans-${selectedPrompt.id}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                <div className="p-4 rounded-2xl bg-accent/5 border border-accent/20 text-xs sm:text-sm text-text leading-relaxed">
                  {selectedPrompt.response}
                </div>

                <div className="relative rounded-2xl bg-[#090d16] border border-border/80 p-4 font-mono text-xs text-emerald-400 overflow-x-auto">
                  <pre>{selectedPrompt.code}</pre>
                </div>
              </motion.div>
            )}

            {activeInspectorTab === "source" && (
              <motion.div
                key={`src-${selectedPrompt.id}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="p-5 rounded-2xl bg-surface-elevated border border-border space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-text flex items-center gap-1.5">
                    <FileText size={14} className="text-accent" />
                    Indexed Vector Document
                  </span>
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                    Similarity: {selectedPrompt.similarity}
                  </span>
                </div>
                <p className="text-xs text-text-secondary bg-bg p-3 rounded-xl border border-border/70 font-mono">
                  {selectedPrompt.source}
                </p>
                <p className="text-[11px] text-text-muted">
                  Vector chunk matched via cosine embedding distance with zero hallucination guarantee.
                </p>
              </motion.div>
            )}

            {activeInspectorTab === "memory" && (
              <motion.div
                key={`mem-${selectedPrompt.id}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="p-5 rounded-2xl bg-surface-elevated border border-border space-y-3"
              >
                <div className="flex items-center gap-2">
                  <Brain size={16} className="text-purple-500" />
                  <span className="text-xs font-bold text-text">Persistent User Context Anchor</span>
                </div>
                <p className="text-xs text-text-secondary bg-bg p-3 rounded-xl border border-border/70 font-mono">
                  {selectedPrompt.memory}
                </p>
                <p className="text-[11px] text-text-muted">
                  Retained automatically across past 1-on-1 sessions to tailor discussions to your background.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
