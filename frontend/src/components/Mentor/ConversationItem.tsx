// src/components/Mentor/ConversationItem.tsx

import React, { useState, useRef, useEffect } from "react";
import { MessageSquare, MoreVertical, Edit3, Archive, Trash2 } from "lucide-react";
import type { MentorConversation } from "../../types/mentor";

interface ConversationItemProps {
  conversation: MentorConversation;
  isActive: boolean;
  onSelect: (id: number) => void;
  onRename: (conversation: MentorConversation) => void;
  onArchive: (conversation: MentorConversation) => void;
  onDelete: (conversation: MentorConversation) => void;
}

export default function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onRename,
  onArchive,
  onDelete,
}: ConversationItemProps) {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    }
    if (showMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showMenu]);

  // Format relative timestamp
  const formatTime = (isoString?: string | null) => {
    if (!isoString) return "";
    const d = new Date(isoString);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) {
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  const timeLabel = formatTime(conversation.last_message_at || conversation.created_at);

  return (
    <div
      onClick={() => onSelect(conversation.id)}
      className={`group relative flex items-center justify-between p-2.5 rounded-xl transition-all cursor-pointer border ${
        isActive
          ? "bg-accent/10 border-accent/30 text-accent font-semibold shadow-xs"
          : "bg-transparent border-transparent hover:bg-bg-alt text-text-secondary hover:text-text"
      }`}
    >
      <div className="flex items-center gap-2.5 min-w-0 flex-1 pr-2">
        <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? "text-accent" : "text-text-secondary"}`} />
        <div className="min-w-0 flex-1">
          <p className="text-xs truncate leading-snug">{conversation.title}</p>
          <div className="flex items-center gap-1.5 text-[10px] text-text-secondary/80 mt-0.5">
            {conversation.status === "ARCHIVED" && (
              <span className="px-1.5 py-0.2 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded text-[9px] font-medium border border-amber-500/20">
                Archived
              </span>
            )}
            <span>{timeLabel}</span>
          </div>
        </div>
      </div>

      {/* Dropdown menu trigger button */}
      <div className="relative shrink-0" ref={menuRef}>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu((prev) => !prev);
          }}
          className="p-1 rounded-lg hover:bg-bg border border-transparent hover:border-border text-text-secondary hover:text-text transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100 cursor-pointer"
          title="Conversation options"
        >
          <MoreVertical className="w-3.5 h-3.5" />
        </button>

        {/* Dropdown Menu */}
        {showMenu && (
          <div className="absolute right-0 top-6 z-30 w-36 bg-bg border border-border rounded-xl shadow-lg py-1 text-xs">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(false);
                onRename(conversation);
              }}
              className="w-full px-3 py-1.5 text-left flex items-center gap-2 hover:bg-bg-alt text-text cursor-pointer"
            >
              <Edit3 className="w-3.5 h-3.5 text-text-secondary" />
              <span>Rename</span>
            </button>

            {conversation.status !== "ARCHIVED" && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(false);
                  onArchive(conversation);
                }}
                className="w-full px-3 py-1.5 text-left flex items-center gap-2 hover:bg-bg-alt text-text cursor-pointer"
              >
                <Archive className="w-3.5 h-3.5 text-amber-500" />
                <span>Archive</span>
              </button>
            )}

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(false);
                onDelete(conversation);
              }}
              className="w-full px-3 py-1.5 text-left flex items-center gap-2 hover:bg-danger/10 text-danger cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
