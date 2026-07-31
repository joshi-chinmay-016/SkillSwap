// src/components/Mentor/RenameConversationDialog.tsx

import React, { useState, useEffect } from "react";
import { Edit3, X } from "lucide-react";

interface RenameConversationDialogProps {
  isOpen: boolean;
  initialTitle: string;
  isPending: boolean;
  onClose: () => void;
  onSave: (newTitle: string) => void;
}

export default function RenameConversationDialog({
  isOpen,
  initialTitle,
  isPending,
  onClose,
  onSave,
}: RenameConversationDialogProps) {
  const [title, setTitle] = useState(initialTitle);

  useEffect(() => {
    setTitle(initialTitle);
  }, [initialTitle, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (title.trim() && !isPending) {
      onSave(title.trim());
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-bg border border-border rounded-2xl shadow-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <Edit3 className="w-4 h-4 text-accent" />
            <h3 className="text-sm font-bold text-text">Rename Conversation</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-text-secondary hover:text-text hover:bg-bg-alt cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Conversation Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Graph Algorithms Revision"
              maxLength={255}
              autoFocus
              className="w-full px-3 py-2 text-xs bg-bg-alt border border-border rounded-xl text-text focus:outline-none focus:border-accent"
            />
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
              type="submit"
              disabled={!title.trim() || isPending}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-accent text-white hover:opacity-90 disabled:opacity-50 cursor-pointer"
            >
              {isPending ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
