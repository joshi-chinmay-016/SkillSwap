// src/components/Mentor/ConfirmActionModal.tsx

import React from "react";
import { AlertTriangle, Archive, Trash2, X } from "lucide-react";
import type { MentorMemory } from "../../types/mentorMemory";

interface ConfirmActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  actionType: "ARCHIVE" | "FORGET" | null;
  memory: MentorMemory | null;
  onConfirm: () => void;
  isLoading?: boolean;
}

export default function ConfirmActionModal({
  isOpen,
  onClose,
  actionType,
  memory,
  onConfirm,
  isLoading = false,
}: ConfirmActionModalProps) {
  if (!isOpen || !actionType || !memory) return null;

  const isArchive = actionType === "ARCHIVE";

  const title = isArchive ? "Archive this memory?" : "Forget this memory?";
  const description = isArchive
    ? "The mentor will no longer use it during sessions, but it will remain stored for record keeping."
    : "The mentor will permanently stop using this memory. This action can be reversed only if the memory is recreated.";

  const confirmText = isArchive ? "Archive" : "Forget";
  const btnColor = isArchive
    ? "bg-amber-500 hover:bg-amber-600 text-white"
    : "bg-rose-500 hover:bg-rose-600 text-white";
  const Icon = isArchive ? Archive : Trash2;

  return (
    <>
      <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 transition-opacity" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md rounded-2xl bg-bg border border-border shadow-2xl p-5 animate-in zoom-in-95 duration-150">
          <div className="flex items-start justify-between gap-3">
            <div className={`p-2.5 rounded-xl border ${isArchive ? "bg-amber-500/10 border-amber-500/20 text-amber-500" : "bg-rose-500/10 border-rose-500/20 text-rose-500"}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-secondary hover:text-text hover:bg-bg-alt transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-3">
            <h3 className="text-base font-bold text-text">{title}</h3>
            <p className="text-xs text-text-secondary mt-1.5 leading-relaxed">{description}</p>

            <div className="mt-3 p-3 rounded-xl bg-bg-alt border border-border text-xs">
              <span className="font-semibold text-text">{memory.title}</span>
            </div>
          </div>

          <div className="mt-5 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-border text-xs font-semibold text-text-secondary hover:text-text hover:bg-bg-alt transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onConfirm}
              disabled={isLoading}
              className={`px-4 py-2 rounded-xl text-xs font-bold shadow-md transition-all cursor-pointer flex items-center gap-1.5 ${btnColor}`}
            >
              <Icon className="w-3.5 h-3.5" />
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
