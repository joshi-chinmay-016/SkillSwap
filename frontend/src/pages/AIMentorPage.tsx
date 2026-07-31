// src/pages/AIMentorPage.tsx

import React, { useState } from "react";
import MentorHeader from "../components/Mentor/MentorHeader";
import ProfileSidebar from "../components/Mentor/ProfileSidebar";
import ConversationView from "../components/Mentor/ConversationView";
import ChatInput from "../components/Mentor/ChatInput";
import SuggestedPrompts from "../components/Mentor/SuggestedPrompts";
import { useAIContext } from "../hooks/useAIContext";
import { useMentorChat } from "../hooks/useMentorChat";
import { SlidersHorizontal, AlertTriangle, RefreshCw } from "lucide-react";

export default function AIMentorPage() {
  const { context, isLoading: isContextLoading, isError: isContextError, refetch } = useAIContext();
  const { messages, sendMessage, clearMessages, isThinking } = useMentorChat();
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-6.5rem)]">
      {/* Outer Card Container */}
      <div className="flex-1 flex flex-col overflow-hidden bg-bg border border-border rounded-2xl shadow-sm">
        {/* Header */}
        <MentorHeader
          onClear={clearMessages}
          hasMessages={messages.length > 0}
          contextVersion={context?.context_version}
        />

        {/* Context Error Banner (Non-blocking fallback) */}
        {isContextError && (
          <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Could not load persistent AI context. Mentor operating in generic mode.</span>
            </div>
            <button
              type="button"
              onClick={() => refetch()}
              className="flex items-center gap-1 text-[11px] font-semibold underline hover:no-underline cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        )}

        {/* Main Work Area: Sidebar + Chat */}
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden relative">
          {/* Mobile Profile Toggle Bar */}
          <div className="lg:hidden px-4 py-2 bg-bg-alt border-b border-border flex items-center justify-between text-xs shrink-0">
            <span className="font-semibold text-text-secondary">Learner Profile Context</span>
            <button
              type="button"
              onClick={() => setShowMobileSidebar(!showMobileSidebar)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-bg border border-border text-text font-medium text-xs cursor-pointer"
            >
              <SlidersHorizontal className="w-3.5 h-3.5 text-accent" />
              <span>{showMobileSidebar ? "Hide Profile" : "View Profile"}</span>
            </button>
          </div>

          {/* Profile Sidebar (Responsive) */}
          <div className={`${showMobileSidebar ? "block" : "hidden"} lg:block`}>
            <ProfileSidebar
              context={context}
              isLoading={isContextLoading}
              onTopicClick={(prompt) => {
                sendMessage(prompt);
                setShowMobileSidebar(false);
              }}
            />
          </div>

          {/* Chat Column */}
          <div className="flex-1 flex flex-col overflow-hidden bg-bg-alt/30">
            <ConversationView
              messages={messages}
              isThinking={isThinking}
              onSendPrompt={sendMessage}
            />

            {/* Quick Suggested Prompts when conversation is active */}
            {messages.length > 0 && (
              <div className="px-4 py-2 bg-bg/80 border-t border-border overflow-x-auto shrink-0">
                <SuggestedPrompts onSelectPrompt={sendMessage} disabled={isThinking} />
              </div>
            )}

            {/* Chat Input */}
            <ChatInput onSend={sendMessage} disabled={isThinking} />
          </div>
        </div>
      </div>
    </div>
  );
}
