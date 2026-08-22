import React, { useState } from "react";
import { Plus, MessageSquare, Search, Archive, AlertCircle, Loader2, PanelLeftClose } from "lucide-react";
import ConversationItem from "./ConversationItem";
import RenameConversationDialog from "./RenameConversationDialog";
import DeleteConversationDialog from "./DeleteConversationDialog";
import {
  useMentorConversations,
  useCreateMentorConversation,
  useRenameMentorConversation,
  useArchiveMentorConversation,
  useDeleteMentorConversation,
} from "../../hooks/useMentorConversations";
import type { MentorConversation } from "../../types/mentor";

interface ConversationSidebarProps {
  activeConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onNewChatCreated: (id: number) => void;
  onCollapse?: () => void;
}

export default function ConversationSidebar({
  activeConversationId,
  onSelectConversation,
  onNewChatCreated,
  onCollapse,
}: ConversationSidebarProps) {
  const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Modals state
  const [renameTarget, setRenameTarget] = useState<MentorConversation | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<MentorConversation | null>(null);

  // React Query hooks
  const { data, isLoading, isError, refetch } = useMentorConversations(filterStatus);
  const createMutation = useCreateMentorConversation();
  const renameMutation = useRenameMentorConversation();
  const archiveMutation = useArchiveMentorConversation();
  const deleteMutation = useDeleteMentorConversation();

  const handleNewChat = () => {
    createMutation.mutate(undefined, {
      onSuccess: (newConv) => {
        onNewChatCreated(newConv.id);
      },
    });
  };

  const handleRenameConfirm = (newTitle: string) => {
    if (!renameTarget) return;
    renameMutation.mutate(
      { conversationId: renameTarget.id, title: newTitle },
      {
        onSuccess: () => {
          setRenameTarget(null);
        },
      }
    );
  };

  const handleArchiveConfirm = (conversation: MentorConversation) => {
    archiveMutation.mutate(conversation.id);
  };

  const handleDeleteConfirm = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate(deleteTarget.id, {
      onSuccess: () => {
        setDeleteTarget(null);
      },
    });
  };

  // Filter conversations locally by title search query
  const conversations = data?.conversations || [];
  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full bg-bg-alt/40 flex flex-col h-full shrink-0 overflow-hidden">
      {/* Sidebar Header & New Chat Button */}
      <div className="p-3 border-b border-border space-y-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleNewChat}
            disabled={createMutation.isPending}
            className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-accent text-white font-semibold text-xs shadow-xs hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50"
          >
            {createMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            <span>New Chat</span>
          </button>

          {onCollapse && (
            <button
              type="button"
              onClick={onCollapse}
              className="p-2 rounded-xl border border-border bg-bg hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-colors shadow-2xs shrink-0"
              title="Collapse chat history"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-text-secondary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-8 pr-3 py-1.5 bg-bg border border-border rounded-xl text-xs text-text focus:outline-none focus:border-accent"
          />
        </div>

        {/* Filter Status Pills */}
        <div className="flex items-center gap-1 text-[11px]">
          <button
            type="button"
            onClick={() => setFilterStatus(undefined)}
            className={`flex-1 py-1 rounded-lg border text-center font-medium transition-colors cursor-pointer ${
              filterStatus === undefined
                ? "bg-accent/10 border-accent/30 text-accent"
                : "bg-bg border-border text-text-secondary hover:text-text"
            }`}
          >
            All
          </button>
          <button
            type="button"
            onClick={() => setFilterStatus("ACTIVE")}
            className={`flex-1 py-1 rounded-lg border text-center font-medium transition-colors cursor-pointer ${
              filterStatus === "ACTIVE"
                ? "bg-accent/10 border-accent/30 text-accent"
                : "bg-bg border-border text-text-secondary hover:text-text"
            }`}
          >
            Active
          </button>
          <button
            type="button"
            onClick={() => setFilterStatus("ARCHIVED")}
            className={`flex-1 py-1 rounded-lg border text-center font-medium transition-colors cursor-pointer ${
              filterStatus === "ARCHIVED"
                ? "bg-accent/10 border-accent/30 text-accent"
                : "bg-bg border-border text-text-secondary hover:text-text"
            }`}
          >
            Archived
          </button>
        </div>
      </div>

      {/* Conversations List Area */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading && (
          <div className="p-4 space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-10 bg-bg/60 border border-border rounded-xl animate-pulse" />
            ))}
          </div>
        )}

        {isError && (
          <div className="p-4 text-center space-y-2 text-xs text-danger">
            <AlertCircle className="w-5 h-5 mx-auto text-danger" />
            <p>Failed to load conversations</p>
            <button
              type="button"
              onClick={() => refetch()}
              className="px-2.5 py-1 rounded-lg bg-bg border border-border text-text font-medium text-[11px] cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {!isLoading && !isError && filteredConversations.length === 0 && (
          <div className="p-6 text-center text-xs text-text-secondary space-y-2">
            <MessageSquare className="w-6 h-6 mx-auto text-text-secondary/50" />
            <p className="font-medium">No conversations found</p>
            <p className="text-[11px] text-text-secondary/70">
              Start a new chat with your AI Mentor to begin learning!
            </p>
          </div>
        )}

        {!isLoading &&
          !isError &&
          filteredConversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={activeConversationId === conv.id}
              onSelect={onSelectConversation}
              onRename={(c) => setRenameTarget(c)}
              onArchive={handleArchiveConfirm}
              onDelete={(c) => setDeleteTarget(c)}
            />
          ))}
      </div>

      {/* Modals */}
      {renameTarget && (
        <RenameConversationDialog
          isOpen={!!renameTarget}
          initialTitle={renameTarget.title}
          isPending={renameMutation.isPending}
          onClose={() => setRenameTarget(null)}
          onSave={handleRenameConfirm}
        />
      )}

      {deleteTarget && (
        <DeleteConversationDialog
          isOpen={!!deleteTarget}
          title={deleteTarget.title}
          isPending={deleteMutation.isPending}
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}
    </div>
  );
}
