// src/components/Mentor/DeleteConversationDialog.tsx

import React from "react";
import { AlertTriangle, X } from "lucide-react";

interface DeleteConversationDialogProps {
  isOpen: boolean;
  title: string;
  isPending: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export default function DeleteConversationDialog({
  isOpen,
  title,
  isPending,
  onClose,
  onConfirm,
}: DeleteConversationDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-bg border border-border rounded-2xl shadow-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2 text-danger">
            <AlertTriangle className="w-4 h-4" />
            <h3 className="text-sm font-bold">Delete Conversation</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-text-secondary hover:text-text hover:bg-bg-alt cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="text-xs text-text-secondary space-y-2">
          <p>
            Are you sure you want to delete <span className="font-semibold text-text">"{title}"</span>?
          </p>
          <p className="text-danger/90">
            This will permanently remove the conversation thread and all stored message history. This action cannot be undone.
          </p>
        </div>

        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-1.5 text-xs font-medium rounded-xl border border-border text-text hover:bg-bg-alt cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isPending}
            onClick={onConfirm}
            className="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-danger text-white hover:opacity-90 disabled:opacity-50 cursor-pointer"
          >
            {isPending ? "Deleting..." : "Delete Permanently"}
          </button>
        </div>
      </div>
    </div>
  );
}
