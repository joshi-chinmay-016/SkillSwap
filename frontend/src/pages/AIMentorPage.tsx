// src/pages/AIMentorPage.tsx

import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import MentorHeader from "../components/Mentor/MentorHeader";
import MentorNavTabs from "../components/Mentor/MentorNavTabs";
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
import { useRAGQuery } from "../hooks/useRAGQuery";
import type { MessageItem } from "../types/mentor";
import { SlidersHorizontal, AlertTriangle, RefreshCw, Lock, Sparkles, BookOpen, ChevronLeft, ChevronRight, MessageSquare } from "lucide-react";

export default function AIMentorPage() {
  const { conversationId: paramId } = useParams<{ conversationId?: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const parsedId = paramId ? parseInt(paramId, 10) : null;
  const conversationId = parsedId && !isNaN(parsedId) ? parsedId : null;

  // Mode state: General AI vs Knowledge Base (RAG)
  const initialMode = searchParams.get("mode") === "knowledge" ? "knowledge" : "general";
  const [aiMode, setAiMode] = useState<"general" | "knowledge">(initialMode);

  // RAG query mutation
  const ragMutation = useRAGQuery();

  // AI Context hook
  const { context, isLoading: isContextLoading, isError: isContextError, refetch: refetchContext } = useAIContext();

  // Mentor conversation queries & mutations
  const { data: activeConversation } = useMentorConversation(conversationId);
  const { data: messagesData } = useMentorMessages(conversationId);
  const sendMutation = useSendMentorMessage(conversationId);
  const retryMutation = useRetryMentorMessage(conversationId);
  const createMutation = useCreateMentorConversation();

  // Drawers & Sidebars UI state
  const [showMobileConvSidebar, setShowMobileConvSidebar] = useState(false);
  const [isDesktopConvSidebarCollapsed, setIsDesktopConvSidebarCollapsed] = useState(false);
  const [showProfileSidebar, setShowProfileSidebar] = useState(false);

  const handleToggleSidebar = () => {
    if (window.innerWidth < 1024) {
      setShowMobileConvSidebar((prev) => !prev);
    } else {
      setIsDesktopConvSidebarCollapsed((prev) => !prev);
    }
  };

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
    <div className="flex flex-col h-full w-full min-h-0">
      {/* Outer Card Container */}
      <div className="flex-1 flex flex-col overflow-hidden bg-bg border border-border rounded-2xl shadow-xs min-h-0">
        {/* Mentor Workspace Navigation Tabs */}
        <MentorNavTabs />

        {/* Header */}
        <MentorHeader
          conversation={activeConversation}
          contextVersion={context?.context_version}
          showProfileSidebar={showProfileSidebar}
          aiMode={aiMode}
          onToggleAiMode={setAiMode}
          onToggleSidebar={handleToggleSidebar}
          onToggleProfileSidebar={() => setShowProfileSidebar(!showProfileSidebar)}
          isSidebarCollapsed={isDesktopConvSidebarCollapsed}
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
        <div className="flex-1 flex overflow-hidden relative w-full min-h-0">
          {/* Mobile Conversations Drawer Backdrop */}
          {showMobileConvSidebar && (
            <div
              className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-xs z-30"
              onClick={() => setShowMobileConvSidebar(false)}
            />
          )}

          {/* Conversations Sidebar (Mobile Slide-over & Desktop Smooth Collapsible) */}
          <div
            className={`fixed lg:relative z-40 lg:z-10 inset-y-0 left-0 bg-bg transition-all duration-300 ease-in-out border-r border-border shrink-0 flex flex-col overflow-hidden ${
              showMobileConvSidebar
                ? "translate-x-0 w-72"
                : "-translate-x-full lg:translate-x-0"
            } ${
              isDesktopConvSidebarCollapsed
                ? "lg:w-0 lg:opacity-0 lg:pointer-events-none lg:border-r-0"
                : "lg:w-64 xl:w-72 lg:opacity-100"
            }`}
          >
            <ConversationSidebar
              activeConversationId={conversationId}
              onSelectConversation={handleSelectConversation}
              onNewChatCreated={handleNewChatCreated}
              onCollapse={() => setIsDesktopConvSidebarCollapsed(true)}
            />
          </div>

          {/* Central Chat Workspace (Dominates width & scales dynamically) */}
          <div className="flex-1 flex flex-col overflow-hidden bg-bg-alt/20 min-w-0 w-full min-h-0">
            {/* Grounded Knowledge Mode Banner */}
            {aiMode === "knowledge" && (
              <div className="px-4 py-2.5 bg-accent/10 border-b border-accent/20 text-accent text-xs flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2 min-w-0">
                  <Sparkles className="w-4 h-4 shrink-0 text-accent" />
                  <span className="font-semibold truncate">
                    Grounded Knowledge Mode: AI Mentor will synthesize answers from your indexed Knowledge Base.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => navigate("/mentor/knowledge?tab=documents")}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-bg border border-accent/30 text-accent hover:bg-accent hover:text-white text-[11px] font-bold transition-colors cursor-pointer shrink-0"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>View Knowledge Library</span>
                </button>
              </div>
            )}

            {/* Read-Only Banner for Archived Conversation */}
            {isArchived && (
              <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex items-center gap-2 shrink-0">
                <Lock className="w-4 h-4 shrink-0" />
                <span>This conversation is archived. You can view message history, but cannot send new messages.</span>
              </div>
            )}

            {/* Main Chat Stream */}
            {!conversationId && (
              <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-10 text-center space-y-6 overflow-y-auto max-w-3xl mx-auto w-full">
                <div className="w-16 h-16 rounded-2xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shadow-xs">
                  <Sparkles className="w-8 h-8" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl sm:text-3xl font-bold text-text tracking-tight">Your AI Mentor Workspace</h2>
                  <p className="text-sm sm:text-base text-text-secondary leading-relaxed max-w-xl mx-auto">
                    Select a conversation from the sidebar or start a brand new persistent thread to receive personalized, learner-aware guidance.
                  </p>
                </div>

                <div className="w-full max-w-2xl pt-2">
                  <SuggestedPrompts
                    onSelectPrompt={(prompt) => handleSendMessage(prompt)}
                    disabled={createMutation.isPending || sendMutation.isPending}
                  />
                </div>
              </div>
            )}

            {conversationId && (
              <div className="flex-1 flex flex-col overflow-hidden w-full max-w-6xl 2xl:max-w-7xl mx-auto min-h-0">
                <ConversationView
                  messages={messages}
                  isThinking={sendMutation.isPending || retryMutation.isPending}
                  onSendPrompt={handleSendMessage}
                />

                {/* Quick Suggested Prompts when conversation is active */}
                {messages.length > 0 && !isArchived && (
                  <div className="px-4 py-1.5 bg-bg/80 border-t border-border overflow-x-auto shrink-0 flex items-center">
                    <SuggestedPrompts
                      onSelectPrompt={handleSendMessage}
                      disabled={sendMutation.isPending || retryMutation.isPending}
                      compact
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
                      : aiMode === "knowledge"
                      ? "Ask AI Mentor using your indexed Knowledge Base (RAG)..."
                      : "Ask your AI Mentor anything..."
                  }
                />
              </div>
            )}
          </div>

          {/* Learner Profile Context Panel (Mobile Modal / Desktop Slide-over) */}
          {showProfileSidebar && (
            <>
              {/* Mobile Overlay */}
              <div
                className="lg:hidden fixed inset-0 bg-black/40 z-30"
                onClick={() => setShowProfileSidebar(false)}
              />

              <div className="fixed lg:relative z-40 lg:z-10 inset-y-0 right-0 h-full bg-bg border-l border-border w-80 shrink-0 shadow-lg lg:shadow-none animate-in slide-in-from-right duration-200">
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}
