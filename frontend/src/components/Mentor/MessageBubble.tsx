// src/components/Mentor/MessageBubble.tsx

import React from "react";
import { Bot, User, AlertTriangle, RefreshCw } from "lucide-react";
import MentorResponseCard from "./MentorResponseCard";
import type { MessageItem } from "../../types/mentor";

interface MessageBubbleProps {
  message: MessageItem;
  onTopicClick?: (topic: string) => void;
  onRetryMessage?: (messageId: number | string) => void;
}

export default function MessageBubble({ message, onTopicClick, onRetryMessage }: MessageBubbleProps) {
  const isUser = message.role.toUpperCase() === "USER";

  const formatTimestamp = (raw?: string) => {
    if (!raw) return "";
    try {
      const d = new Date(raw);
      if (isNaN(d.getTime())) return raw;
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return raw;
    }
  };

  const timeLabel = formatTimestamp(message.created_at || message.timestamp);

  if (message.isError) {
    return (
      <div className="flex gap-3 justify-start items-start">
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-danger/10 border border-danger/20 text-danger flex items-center justify-center shadow-xs">
          <AlertTriangle className="w-4 h-4" />
        </div>
        <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl rounded-tl-sm px-4 py-3 bg-danger/10 border border-danger/20 text-danger text-xs space-y-2">
          <p className="font-semibold">Response Error</p>
          <p>{message.content}</p>
          {onRetryMessage && message.id && (
            <button
              type="button"
              onClick={() => onRetryMessage(message.id)}
              className="flex items-center gap-1 text-[11px] font-semibold text-danger hover:underline cursor-pointer pt-1"
            >
              <RefreshCw className="w-3 h-3" /> Retry Generation
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 items-start ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shadow-xs">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div
        className={`max-w-[88%] sm:max-w-[80%] rounded-2xl px-4 py-3 shadow-xs ${
          isUser
            ? "bg-accent text-white rounded-tr-sm"
            : "bg-bg border border-border rounded-tl-sm"
        }`}
      >
        {isUser ? (
          <div>
            <p className="text-xs leading-relaxed whitespace-pre-wrap">{message.content}</p>
            {timeLabel && (
              <span className="block text-[10px] text-white/70 text-right mt-1 font-mono">
                {timeLabel}
              </span>
            )}
          </div>
        ) : (
          <div>
            <MentorResponseCard
              content={message.content}
              recommendedTopics={message.recommended_topics}
              difficultyLevel={message.difficulty_level}
              onTopicClick={onTopicClick}
            />
            {timeLabel && (
              <span className="block text-[10px] text-text-secondary text-right mt-2 font-mono">
                {timeLabel}
              </span>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-accent text-white flex items-center justify-center shadow-xs font-bold text-xs">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
}
