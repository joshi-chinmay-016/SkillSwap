import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ArrowLeftRight, Code, Palette, Zap, Sparkles, CheckCircle2, UserCheck } from "lucide-react";

export default function SkillExchangeVisualizer() {
  const [activeTab, setActiveTab] = useState("live");

  const exchanges = [
    {
      id: 1,
      userA: { name: "Alex Chen", teaches: "Python & FastAPI", wants: "UI / UX Design", avatarBg: "from-blue-500 to-indigo-600" },
      userB: { name: "Sarah Miller", teaches: "UI / UX Design", wants: "Python & FastAPI", avatarBg: "from-pink-500 to-rose-600" },
      topic: "Building an AI-Powered Dashboard",
      skillCoins: "+10 Skill Coins Exchanged",
    },
    {
      id: 2,
      userA: { name: "Devon Vance", teaches: "System Design & SQL", wants: "React & Next.js", avatarBg: "from-amber-500 to-orange-600" },
      userB: { name: "Priya Sharma", teaches: "React & Next.js", wants: "System Design & SQL", avatarBg: "from-emerald-500 to-teal-600" },
      topic: "High-Concurrency Web Architecture",
      skillCoins: "+10 Skill Coins Exchanged",
    },
  ];

  const [selectedExchange, setSelectedExchange] = useState(exchanges[0]);

  return (
    <div className="w-full max-w-5xl mx-auto rounded-3xl border border-card-border bg-card-bg/90 backdrop-blur-xl p-6 sm:p-10 shadow-xl overflow-hidden relative">
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-10">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-semibold uppercase tracking-wider mb-3">
          <ArrowLeftRight size={13} />
          <span>Bilateral Knowledge Exchange</span>
        </div>
        <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-text">
          How Peers Swap Knowledge in Real Time
        </h3>
        <p className="text-sm text-text-secondary mt-2">
          No monetary barriers. Teach what you excel at, earn Skill Coins, and spend them to master new capabilities from experienced peers.
        </p>
      </div>

      {/* Exchange Selector Tabs */}
      <div className="flex items-center justify-center gap-3 mb-10">
        {exchanges.map((item) => (
          <button
            key={item.id}
            onClick={() => setSelectedExchange(item)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 cursor-pointer ${
              selectedExchange.id === item.id
                ? "bg-accent text-white shadow-glow"
                : "bg-surface-elevated text-text-secondary hover:text-text border border-border"
            }`}
          >
            {item.userA.teaches} ↔ {item.userB.teaches}
          </button>
        ))}
      </div>

      {/* Interactive Visual Graph */}
      <div className="relative grid grid-cols-1 md:grid-cols-7 gap-6 items-center">
        {/* Peer A Card */}
        <motion.div
          key={`peerA-${selectedExchange.id}`}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className="md:col-span-3 rounded-2xl border border-border/90 bg-surface-elevated p-6 shadow-sm space-y-4 hover:border-accent/40 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${selectedExchange.userA.avatarBg} flex items-center justify-center text-white font-bold text-lg shadow-sm`}>
              {selectedExchange.userA.name.charAt(0)}
            </div>
            <div>
              <h4 className="font-bold text-text text-base">{selectedExchange.userA.name}</h4>
              <span className="inline-flex items-center gap-1 text-[11px] text-emerald-500 font-medium">
                <UserCheck size={12} /> Verified Peer
              </span>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-border/70 text-xs">
            <div>
              <span className="text-text-muted font-medium block mb-1">Teaches (Offering):</span>
              <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-semibold inline-block">
                {selectedExchange.userA.teaches}
              </span>
            </div>
            <div>
              <span className="text-text-muted font-medium block mb-1">Wants to Learn:</span>
              <span className="px-2.5 py-1 rounded-lg bg-accent/10 border border-accent/20 text-accent font-semibold inline-block">
                {selectedExchange.userA.wants}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Center Exchange Connector */}
        <div className="md:col-span-1 flex flex-col items-center justify-center text-center py-4 md:py-0">
          <div className="relative">
            <motion.div
              animate={{ rotate: [0, 180, 360] }}
              transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
              className="w-14 h-14 rounded-full bg-gradient-to-tr from-accent to-purple-600 p-[2px] shadow-glow"
            >
              <div className="w-full h-full bg-bg rounded-full flex items-center justify-center">
                <ArrowLeftRight className="text-accent" size={22} />
              </div>
            </motion.div>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-accent mt-3 px-2 py-0.5 rounded-full bg-accent/10 border border-accent/20">
            1:1 Session
          </span>
        </div>

        {/* Peer B Card */}
        <motion.div
          key={`peerB-${selectedExchange.id}`}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className="md:col-span-3 rounded-2xl border border-border/90 bg-surface-elevated p-6 shadow-sm space-y-4 hover:border-accent/40 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${selectedExchange.userB.avatarBg} flex items-center justify-center text-white font-bold text-lg shadow-sm`}>
              {selectedExchange.userB.name.charAt(0)}
            </div>
            <div>
              <h4 className="font-bold text-text text-base">{selectedExchange.userB.name}</h4>
              <span className="inline-flex items-center gap-1 text-[11px] text-emerald-500 font-medium">
                <UserCheck size={12} /> Verified Peer
              </span>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-border/70 text-xs">
            <div>
              <span className="text-text-muted font-medium block mb-1">Teaches (Offering):</span>
              <span className="px-2.5 py-1 rounded-lg bg-pink-500/10 border border-pink-500/20 text-pink-600 dark:text-pink-400 font-semibold inline-block">
                {selectedExchange.userB.teaches}
              </span>
            </div>
            <div>
              <span className="text-text-muted font-medium block mb-1">Wants to Learn:</span>
              <span className="px-2.5 py-1 rounded-lg bg-accent/10 border border-accent/20 text-accent font-semibold inline-block">
                {selectedExchange.userB.wants}
              </span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom Session Outcome Banner */}
      <div className="mt-8 rounded-xl bg-accent/5 border border-accent/20 p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-text">
          <Zap size={16} className="text-accent shrink-0" />
          <span><strong>Focus Topic:</strong> {selectedExchange.topic}</span>
        </div>
        <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold">
          {selectedExchange.skillCoins}
        </span>
      </div>
    </div>
  );
}
