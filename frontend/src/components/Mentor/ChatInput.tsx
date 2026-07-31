// src/components/Mentor/ChatInput.tsx

import React, { useState, useRef, useEffect } from "react";
import { Send, CornerDownLeft } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const MAX_CHARS = 4000;

export default function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask your AI Mentor anything...",
}: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  return (
    <div className="p-3 bg-bg border-t border-border shrink-0">
      <div className="relative flex items-end gap-2 bg-bg-alt border border-border focus-within:border-accent/60 focus-within:ring-1 focus-within:ring-accent/30 rounded-xl p-2 transition-all">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent border-0 resize-none text-xs text-text placeholder:text-text-secondary focus:outline-none focus:ring-0 max-h-40 min-h-[38px] p-2 leading-relaxed"
        />

        <div className="flex items-center gap-2 pb-1 pr-1 shrink-0">
          <span
            className={`text-[10px] font-mono ${
              text.length >= MAX_CHARS ? "text-danger font-bold" : "text-text-secondary opacity-60"
            }`}
          >
            {text.length}/{MAX_CHARS}
          </span>

          <button
            type="button"
            onClick={handleSend}
            disabled={!text.trim() || disabled}
            className="p-2 rounded-lg bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-xs cursor-pointer"
            title="Send message (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between mt-2 px-1 text-[10px] text-text-secondary opacity-70">
        <span className="flex items-center gap-1">
          <CornerDownLeft className="w-3 h-3" /> Press <kbd className="px-1 py-0.5 rounded bg-bg-alt border border-border">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-bg-alt border border-border">Shift+Enter</kbd> for new line
        </span>
        <span>Context Active</span>
      </div>
    </div>
  );
}
