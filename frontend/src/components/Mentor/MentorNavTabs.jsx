import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { MessageSquare, BookOpen, Brain, Sparkles } from "lucide-react";

export default function MentorNavTabs() {
  const location = useLocation();

  const isChatActive =
    location.pathname === "/mentor" ||
    (location.pathname.startsWith("/mentor/") &&
      !location.pathname.startsWith("/mentor/knowledge") &&
      !location.pathname.startsWith("/mentor/memory"));

  const isKnowledgeActive = location.pathname.startsWith("/mentor/knowledge");
  const isMemoryActive = location.pathname.startsWith("/mentor/memory");

  return (
    <div className="bg-bg border-b border-border px-4 py-2.5 flex items-center justify-between gap-4 shrink-0">
      {/* Primary Tabs */}
      <div className="flex items-center gap-1 bg-bg-alt/60 p-1 rounded-xl border border-border/60">
        <NavLink
          to="/mentor"
          end
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            isChatActive
              ? "bg-bg text-accent shadow-xs border border-border/80 font-bold"
              : "text-text-secondary hover:text-text hover:bg-bg/40"
          }`}
        >
          <MessageSquare size={14} />
          <span>Chat</span>
        </NavLink>

        <NavLink
          to="/mentor/knowledge"
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            isKnowledgeActive
              ? "bg-bg text-accent shadow-xs border border-border/80 font-bold"
              : "text-text-secondary hover:text-text hover:bg-bg/40"
          }`}
        >
          <BookOpen size={14} />
          <span>Knowledge</span>
        </NavLink>

        <NavLink
          to="/mentor/memory"
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            isMemoryActive
              ? "bg-bg text-accent shadow-xs border border-border/80 font-bold"
              : "text-text-secondary hover:text-text hover:bg-bg/40"
          }`}
        >
          <Brain size={14} />
          <span>Memory</span>
        </NavLink>
      </div>

      {/* Mode Indicator Badge */}
      <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-text-secondary">
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        {isKnowledgeActive ? (
          <span className="flex items-center gap-1.5 font-semibold text-accent">
            <Sparkles size={13} />
            <span>Grounded Knowledge Mode (RAG & Library)</span>
          </span>
        ) : isMemoryActive ? (
          <span className="font-semibold text-text">What Mentor Remembers About You</span>
        ) : (
          <span className="font-semibold text-text">Learner-Aware Conversation</span>
        )}
      </div>
    </div>
  );
}
