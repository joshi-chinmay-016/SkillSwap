// src/components/Mentor/MentorHeader.tsx

import React from "react";
import { Bot, Sparkles, Layers, Menu, Lock } from "lucide-react";
import type { MentorConversation } from "../../types/mentor";

interface MentorHeaderProps {
  conversation?: MentorConversation | null;
  contextVersion?: number;
  showProfileSidebar?: boolean;
  onToggleSidebar?: () => void;
  onToggleProfileSidebar?: () => void;
}

export default function MentorHeader({
  conversation,
  contextVersion = 1,
  showProfileSidebar = false,
  onToggleSidebar,
  onToggleProfileSidebar,
}: MentorHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-3 p-3.5 bg-bg border-b border-border shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        {/* Mobile Sidebar Toggle Button */}
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="lg:hidden p-2 rounded-xl border border-border text-text-secondary hover:text-text hover:bg-bg-alt cursor-pointer"
            title="Toggle Conversations"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <div className="relative shrink-0">
          <div className="w-9 h-9 rounded-xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shadow-xs">
            <Bot className="w-5 h-5" />
          </div>
          <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold text-text truncate tracking-tight">
              {conversation ? conversation.title : "AI Learning Mentor"}
            </h1>
            {conversation?.status === "ARCHIVED" ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                <Lock className="w-3 h-3" /> Archived
              </span>
            ) : (
              <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-accent/10 text-accent border border-accent/15">
                <Sparkles className="w-3 h-3" /> Persistent Mentor
              </span>
            )}
          </div>
          <p className="text-[11px] text-text-secondary truncate">
            {conversation
              ? "Context & Conversation-Aware Mentor Workspace"
              : "Select or start a conversation thread"}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {onToggleProfileSidebar && (
          <button
            type="button"
            onClick={onToggleProfileSidebar}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all cursor-pointer ${
              showProfileSidebar
                ? "bg-accent/10 border-accent/30 text-accent font-semibold shadow-xs"
                : "bg-bg-alt border-border text-text-secondary hover:text-text hover:bg-bg"
            }`}
            title={showProfileSidebar ? "Hide Profile Panel" : "View Profile Panel"}
          >
            <Layers className="w-3.5 h-3.5 text-accent" />
            <span>Profile v{contextVersion}</span>
          </button>
        )}
      </div>
    </div>
  );
}
