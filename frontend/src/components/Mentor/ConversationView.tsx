// src/components/Mentor/ConversationView.tsx

import React, { useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import EmptyConversation from "./EmptyConversation";
import SuggestedPrompts from "./SuggestedPrompts";
import type { MessageItem } from "../../types/mentor";

interface ConversationViewProps {
  messages: MessageItem[];
  isThinking: boolean;
  onSendPrompt: (prompt: string) => void;
}

export default function ConversationView({
  messages,
  isThinking,
  onSendPrompt,
}: ConversationViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Smooth scroll to bottom whenever messages change or typing state changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto p-4 flex flex-col justify-center">
        <EmptyConversation onSelectPrompt={onSendPrompt} disabled={isThinking} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onTopicClick={onSendPrompt} />
      ))}

      {isThinking && <TypingIndicator />}

      <div ref={bottomRef} />
    </div>
  );
}
