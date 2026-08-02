// src/components/Mentor/MemorySettingsModal.tsx

import React from "react";
import { X, Settings, Info, Save } from "lucide-react";
import type { MentorMemorySettings } from "../../types/mentorMemory";

interface MemorySettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings?: MentorMemorySettings | null;
  onSave: (payload: Partial<MentorMemorySettings>) => void;
  isLoading?: boolean;
}

export default function MemorySettingsModal({
  isOpen,
  onClose,
  settings,
  onSave,
  isLoading = false,
}: MemorySettingsModalProps) {
  if (!isOpen) return null;

  const currentSettings = settings || {
    memory_enabled: true,
    automatic_extraction: true,
    automatic_updates: true,
    memory_notifications: true,
  };

  const handleToggle = (key: keyof MentorMemorySettings) => {
    onSave({
      [key]: !currentSettings[key],
    });
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 transition-opacity" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="w-full max-w-lg rounded-2xl bg-bg border border-border shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2 text-text font-bold text-sm">
              <Settings className="w-4 h-4 text-accent" />
              <span>AI Memory Settings & Controls</span>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-secondary hover:text-text hover:bg-bg-alt transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-5 space-y-5">
            {/* Explanatory Info Card (Part 19) */}
            <div className="p-4 rounded-2xl bg-accent/5 border border-accent/15 flex items-start gap-3">
              <Info className="w-5 h-5 text-accent shrink-0 mt-0.5" />
              <div className="text-xs">
                <h4 className="font-bold text-text">How AI Memory Works</h4>
                <p className="text-text-secondary mt-1 leading-relaxed">
                  The mentor remembers durable learning preferences to personalize future sessions. You remain in complete control of every stored memory.
                </p>
              </div>
            </div>

            {/* Controls List (Part 18) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-bg-alt">
                <div>
                  <h4 className="text-xs font-bold text-text">Memory Enabled</h4>
                  <p className="text-[11px] text-text-secondary">
                    Allow mentor to use long-term memory for personalization
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={currentSettings.memory_enabled}
                  onChange={() => handleToggle("memory_enabled")}
                  className="w-4 h-4 accent-accent rounded cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-bg-alt">
                <div>
                  <h4 className="text-xs font-bold text-text">Automatic Extraction</h4>
                  <p className="text-[11px] text-text-secondary">
                    Extract learning preferences automatically after sessions
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={currentSettings.automatic_extraction}
                  onChange={() => handleToggle("automatic_extraction")}
                  className="w-4 h-4 accent-accent rounded cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-bg-alt">
                <div>
                  <h4 className="text-xs font-bold text-text">Automatic Updates</h4>
                  <p className="text-[11px] text-text-secondary">
                    Update existing memories when new insights are discovered
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={currentSettings.automatic_updates}
                  onChange={() => handleToggle("automatic_updates")}
                  className="w-4 h-4 accent-accent rounded cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-bg-alt">
                <div>
                  <h4 className="text-xs font-bold text-text">Memory Notifications</h4>
                  <p className="text-[11px] text-text-secondary">
                    Notify when important memories are learned or updated
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={currentSettings.memory_notifications}
                  onChange={() => handleToggle("memory_notifications")}
                  className="w-4 h-4 accent-accent rounded cursor-pointer"
                />
              </div>
            </div>
          </div>

          <div className="p-4 border-t border-border flex items-center justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-accent text-white font-bold text-xs shadow-md hover:bg-accent/90 transition-all cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
