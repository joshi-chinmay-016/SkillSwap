// src/pages/MentorMemoryPage.tsx

import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Brain, ArrowLeft, Settings, RefreshCw, AlertCircle, Sparkles } from "lucide-react";
import {
  useMentorMemory,
  useMemoryStats,
  useMemorySettings,
  useUpdateMemory,
  useArchiveMemory,
  useDeleteMemory,
  usePinMemory,
  useCreateMemory,
  useUpdateMemorySettings,
} from "../hooks/useMentorMemory";
import type { MentorMemory } from "../types/mentorMemory";

import MemoryStatistics from "../components/Mentor/MemoryStatistics";
import MemorySearch from "../components/Mentor/MemorySearch";
import MemoryFilters from "../components/Mentor/MemoryFilters";
import MemoryList from "../components/Mentor/MemoryList";
import MemoryDetailsDrawer from "../components/Mentor/MemoryDetailsDrawer";
import EditMemoryModal from "../components/Mentor/EditMemoryModal";
import ConfirmActionModal from "../components/Mentor/ConfirmActionModal";
import MemorySettingsModal from "../components/Mentor/MemorySettingsModal";

export default function MentorMemoryPage() {
  const [activeCategory, setActiveCategory] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ACTIVE");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals & Drawers state
  const [selectedMemory, setSelectedMemory] = useState<MentorMemory | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState<boolean>(false);

  const [editMemory, setEditMemory] = useState<MentorMemory | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);

  const [confirmMemory, setConfirmMemory] = useState<MentorMemory | null>(null);
  const [confirmAction, setConfirmAction] = useState<"ARCHIVE" | "FORGET" | null>(null);

  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Queries
  const memoryFilters = {
    category: activeCategory,
    status: statusFilter,
    search: searchQuery.trim() || undefined,
  };

  const {
    data: memoryListResponse,
    isLoading: isMemoriesLoading,
    isError: isMemoriesError,
    refetch: refetchMemories,
  } = useMentorMemory(memoryFilters);

  const { data: statsData, isLoading: isStatsLoading } = useMemoryStats();
  const { data: settingsData } = useMemorySettings();

  // Mutations
  const createMemoryMutation = useCreateMemory();
  const updateMemoryMutation = useUpdateMemory();
  const archiveMemoryMutation = useArchiveMemory();
  const deleteMemoryMutation = useDeleteMemory();
  const pinMemoryMutation = usePinMemory();
  const updateSettingsMutation = useUpdateMemorySettings();

  const memories = memoryListResponse?.memories ?? [];

  // Handlers
  const handleViewDetails = (memory: MentorMemory) => {
    setSelectedMemory(memory);
    setIsDetailsOpen(true);
  };

  const handleOpenEdit = (memory?: MentorMemory) => {
    setEditMemory(memory || null);
    setIsEditModalOpen(true);
  };

  const handleSaveMemory = (payload: {
    id?: number;
    title: string;
    content: string;
    category: string;
    importance: string;
  }) => {
    if (payload.id) {
      updateMemoryMutation.mutate(
        {
          id: payload.id,
          data: {
            title: payload.title,
            content: payload.content,
            category: payload.category,
            importance: payload.importance,
          },
        },
        {
          onSuccess: () => {
            setIsEditModalOpen(false);
            if (selectedMemory?.id === payload.id) {
              setSelectedMemory((prev) =>
                prev
                  ? {
                      ...prev,
                      title: payload.title,
                      content: payload.content,
                      category: payload.category,
                      importance: payload.importance,
                    }
                  : null
              );
            }
          },
        }
      );
    } else {
      createMemoryMutation.mutate(
        {
          title: payload.title,
          content: payload.content,
          category: payload.category,
          importance: payload.importance,
          source: "Manual",
        },
        {
          onSuccess: () => {
            setIsEditModalOpen(false);
          },
        }
      );
    }
  };

  const handleOpenArchive = (memory: MentorMemory) => {
    setConfirmMemory(memory);
    setConfirmAction("ARCHIVE");
  };

  const handleOpenForget = (memory: MentorMemory) => {
    setConfirmMemory(memory);
    setConfirmAction("FORGET");
  };

  const handleConfirmAction = () => {
    if (!confirmMemory || !confirmAction) return;

    if (confirmAction === "ARCHIVE") {
      archiveMemoryMutation.mutate(confirmMemory.id, {
        onSuccess: () => {
          setConfirmMemory(null);
          setConfirmAction(null);
          if (selectedMemory?.id === confirmMemory.id) {
            setIsDetailsOpen(false);
          }
        },
      });
    } else if (confirmAction === "FORGET") {
      deleteMemoryMutation.mutate(confirmMemory.id, {
        onSuccess: () => {
          setConfirmMemory(null);
          setConfirmAction(null);
          if (selectedMemory?.id === confirmMemory.id) {
            setIsDetailsOpen(false);
          }
        },
      });
    }
  };

  const handleTogglePin = (memory: MentorMemory) => {
    pinMemoryMutation.mutate(
      { id: memory.id, isPinned: !memory.is_pinned },
      {
        onSuccess: () => {
          if (selectedMemory?.id === memory.id) {
            setSelectedMemory((prev) => (prev ? { ...prev, is_pinned: !prev.is_pinned } : null));
          }
        },
      }
    );
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-3xl bg-bg border border-border shadow-xs">
        <div className="flex items-center gap-3.5">
          <Link
            to="/mentor"
            className="p-2.5 rounded-2xl border border-border bg-bg-alt text-text-secondary hover:text-text hover:border-accent/30 transition-all cursor-pointer"
            title="Back to AI Mentor Chat"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="w-10 h-10 rounded-2xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center shrink-0">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-extrabold text-text tracking-tight">AI Memory</h1>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-accent/10 text-accent border border-accent/20">
                <Sparkles className="w-3 h-3" /> Transparency & Control
              </span>
            </div>
            <p className="text-xs text-text-secondary">
              View, manage, and control what your AI Mentor remembers about you.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-border bg-bg-alt text-xs font-semibold text-text hover:bg-bg transition-colors cursor-pointer"
          >
            <Settings className="w-4 h-4 text-accent" />
            <span>Memory Settings</span>
          </button>
        </div>
      </div>

      {/* Part 2 — Memory Dashboard Statistics */}
      <MemoryStatistics stats={statsData} isLoading={isStatsLoading} />

      {/* Main Search & Filters Bar */}
      <div className="p-4 rounded-2xl bg-bg border border-border space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <MemorySearch value={searchQuery} onChange={setSearchQuery} />
        </div>

        <MemoryFilters
          activeCategory={activeCategory}
          onSelectCategory={setActiveCategory}
          statusFilter={statusFilter}
          onSelectStatus={setStatusFilter}
        />
      </div>

      {/* Error State */}
      {isMemoriesError ? (
        <div className="p-8 rounded-3xl border border-rose-500/20 bg-rose-500/5 text-center space-y-3">
          <div className="w-10 h-10 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center mx-auto">
            <AlertCircle className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-text">Unable to load AI Memory</h3>
          <p className="text-xs text-text-secondary">
            Something went wrong while connecting to the memory service.
          </p>
          <button
            type="button"
            onClick={() => refetchMemories()}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-accent text-white font-bold text-xs shadow-md hover:bg-accent/90 transition-all cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      ) : (
        /* PART 3 & 4 — Memory List View */
        <MemoryList
          memories={memories}
          isLoading={isMemoriesLoading}
          onView={handleViewDetails}
          onEdit={handleOpenEdit}
          onArchive={handleOpenArchive}
          onForget={handleOpenForget}
          onTogglePin={handleTogglePin}
          onAddManual={() => handleOpenEdit()}
          isSearchOrFilterActive={activeCategory !== "ALL" || Boolean(searchQuery.trim())}
          onClearFilters={() => {
            setActiveCategory("ALL");
            setSearchQuery("");
          }}
        />
      )}

      {/* PART 7 & 8 — Memory Details Drawer */}
      <MemoryDetailsDrawer
        memory={selectedMemory}
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        onEdit={handleOpenEdit}
        onArchive={handleOpenArchive}
        onForget={handleOpenForget}
        onTogglePin={handleTogglePin}
      />

      {/* PART 9 — Edit / Create Memory Modal */}
      <EditMemoryModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        memory={editMemory}
        onSave={handleSaveMemory}
        isLoading={createMemoryMutation.isPending || updateMemoryMutation.isPending}
      />

      {/* PART 10 & 11 — Confirm Action Modal */}
      <ConfirmActionModal
        isOpen={Boolean(confirmAction)}
        onClose={() => {
          setConfirmAction(null);
          setConfirmMemory(null);
        }}
        actionType={confirmAction}
        memory={confirmMemory}
        onConfirm={handleConfirmAction}
        isLoading={archiveMemoryMutation.isPending || deleteMemoryMutation.isPending}
      />

      {/* PART 18 & 19 — Settings Modal */}
      <MemorySettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settingsData}
        onSave={(data) => updateSettingsMutation.mutate(data)}
        isLoading={updateSettingsMutation.isPending}
      />
    </div>
  );
}
