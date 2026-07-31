// src/pages/AIMentorPage.tsx

import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import MentorHeader from "../components/Mentor/MentorHeader";
import ProfileSidebar from "../components/Mentor/ProfileSidebar";
import ConversationSidebar from "../components/Mentor/ConversationSidebar";
import ConversationView from "../components/Mentor/ConversationView";
import ChatInput from "../components/Mentor/ChatInput";
import SuggestedPrompts from "../components/Mentor/SuggestedPrompts";
import { useAIContext } from "../hooks/useAIContext";
import {
  useMentorConversation,
  useMentorMessages,
  useSendMentorMessage,
  useRetryMentorMessage,
  useCreateMentorConversation,
} from "../hooks/useMentorConversations";
import type { MessageItem } from "../types/mentor";
import { SlidersHorizontal, AlertTriangle, RefreshCw, Lock, Sparkles } from "lucide-react";

export default function AIMentorPage() {
  const { conversationId: paramId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();

  const parsedId = paramId ? parseInt(paramId, 10) : null;
  const conversationId = parsedId && !isNaN(parsedId) ? parsedId : null;

  // AI Context hook
  const { context, isLoading: isContextLoading, isError: isContextError, refetch: refetchContext } = useAIContext();

  // Mentor conversation queries & mutations
  const { data: activeConversation } = useMentorConversation(conversationId);
  const { data: messagesData } = useMentorMessages(conversationId);
  const sendMutation = useSendMentorMessage(conversationId);
  const retryMutation = useRetryMentorMessage(conversationId);
  const createMutation = useCreateMentorConversation();

  // Drawers UI state: profile sidebar defaults to collapsed so chat workspace dominates
  const [showMobileConvSidebar, setShowMobileConvSidebar] = useState(false);
  const [showProfileSidebar, setShowProfileSidebar] = useState(false);

  const isArchived = activeConversation?.status === "ARCHIVED";

  // Map backend MentorMessage list to MessageItem UI models
  const messages: MessageItem[] = (messagesData?.messages || []).map((msg) => ({
    id: msg.id,
    role: msg.role.toLowerCase() === "user" ? "user" : "assistant",
    content: msg.content,
    created_at: msg.created_at,
    timestamp: new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }));

  // Handle user sending a message
  const handleSendMessage = (text: string) => {
    if (!text.trim()) return;

    if (!conversationId) {
      createMutation.mutate(
        { title: text.slice(0, 30) },
        {
          onSuccess: (newConv) => {
            navigate(`/mentor/${newConv.id}`);
            setTimeout(() => {
              sendMutation.mutate(text);
            }, 100);
          },
        }
      );
      return;
    }

    sendMutation.mutate(text);
  };

  const handleSelectConversation = (id: number) => {
    navigate(`/mentor/${id}`);
    setShowMobileConvSidebar(false);
  };

  const handleNewChatCreated = (id: number) => {
    navigate(`/mentor/${id}`);
    setShowMobileConvSidebar(false);
  };

  const handleRetryMessage = (msgId: number | string) => {
    if (typeof msgId === "number" && conversationId) {
      retryMutation.mutate(msgId);
    }
  };

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-6.5rem)]">
      {/* Outer Card Container */}
      <div className="flex-1 flex flex-col overflow-hidden bg-bg border border-border rounded-2xl shadow-sm">
        {/* Header */}
        <MentorHeader
          conversation={activeConversation}
          contextVersion={context?.context_version}
          showProfileSidebar={showProfileSidebar}
          onToggleSidebar={() => setShowMobileConvSidebar(!showMobileConvSidebar)}
          onToggleProfileSidebar={() => setShowProfileSidebar(!showProfileSidebar)}
        />

        {/* Context Error Banner (Non-blocking fallback) */}
        {isContextError && (
          <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Could not load persistent AI context. Mentor operating in general mode.</span>
            </div>
            <button
              type="button"
              onClick={() => refetchContext()}
              className="flex items-center gap-1 text-[11px] font-semibold underline hover:no-underline cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        )}

        {/* Main Work Area: Conversations Sidebar + Expanded Chat Workspace + Collapsible Profile Sidebar */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Slide-over / Desktop Conversations Sidebar */}
          <div
            className={`absolute lg:relative z-20 inset-y-0 left-0 bg-bg transition-transform duration-200 ${
              showMobileConvSidebar ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
            }`}
          >
            <ConversationSidebar
              activeConversationId={conversationId}
              onSelectConversation={handleSelectConversation}
              onNewChatCreated={handleNewChatCreated}
            />
          </div>

          {/* Mobile Overlay backdrop when conversation sidebar is open */}
          {showMobileConvSidebar && (
            <div
              className="lg:hidden absolute inset-0 bg-black/40 z-10"
              onClick={() => setShowMobileConvSidebar(false)}
            />
          )}

          {/* Central Chat Workspace (Takes full width when profile sidebar is collapsed) */}
          <div className="flex-1 flex flex-col overflow-hidden bg-bg-alt/30 min-w-0">
            {/* Read-Only Banner for Archived Conversation */}
            {isArchived && (
              <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex items-center gap-2">
                <Lock className="w-4 h-4 shrink-0" />
                <span>This conversation is archived. You can view message history, but cannot send new messages.</span>
              </div>
            )}

            {/* Main Chat Stream */}
            {!conversationId && (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-4">
                <div className="w-16 h-16 rounded-2xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shadow-xs">
                  <Sparkles className="w-8 h-8" />
                </div>
                <div className="max-w-md space-y-2">
                  <h2 className="text-xl font-bold text-text">Your AI Mentor Workspace</h2>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    Select a conversation from the sidebar or start a brand new persistent thread to receive personalized, learner-aware guidance.
                  </p>
                </div>

                <div className="w-full max-w-lg pt-4">
                  <SuggestedPrompts
                    onSelectPrompt={(prompt) => handleSendMessage(prompt)}
                    disabled={createMutation.isPending || sendMutation.isPending}
                  />
                </div>
              </div>
            )}

            {conversationId && (
              <>
                <ConversationView
                  messages={messages}
                  isThinking={sendMutation.isPending || retryMutation.isPending}
                  onSendPrompt={handleSendMessage}
                />

                {/* Quick Suggested Prompts when conversation is active */}
                {messages.length > 0 && !isArchived && (
                  <div className="px-4 py-2 bg-bg/80 border-t border-border overflow-x-auto shrink-0">
                    <SuggestedPrompts
                      onSelectPrompt={handleSendMessage}
                      disabled={sendMutation.isPending || retryMutation.isPending}
                    />
                  </div>
                )}

                {/* Chat Input Area */}
                <ChatInput
                  onSend={handleSendMessage}
                  disabled={isArchived || sendMutation.isPending || retryMutation.isPending}
                  placeholder={
                    isArchived
                      ? "Conversation is archived (read-only)"
                      : "Ask your AI Mentor anything..."
                  }
                />
              </>
            )}
          </div>

          {/* Learner Profile Context Panel (Collapsible) */}
          {showProfileSidebar && (
            <div className="shrink-0 h-full animate-in slide-in-from-right duration-200">
              <ProfileSidebar
                context={context}
                isLoading={isContextLoading}
                onClose={() => setShowProfileSidebar(false)}
                onTopicClick={(prompt) => {
                  handleSendMessage(prompt);
                  setShowProfileSidebar(false);
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
