// src/components/Mentor/EditMemoryModal.tsx

import React, { useState, useEffect } from "react";
import { X, Save, Plus } from "lucide-react";
import type { MentorMemory, MemoryCategory, MemoryImportance } from "../../types/mentorMemory";
import { MEMORY_CATEGORIES } from "./MemoryFilters";

interface EditMemoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  memory?: MentorMemory | null;
  onSave: (payload: {
    id?: number;
    title: string;
    content: string;
    category: string;
    importance: string;
  }) => void;
  isLoading?: boolean;
}

export default function EditMemoryModal({
  isOpen,
  onClose,
  memory,
  onSave,
  isLoading = false,
}: EditMemoryModalProps) {
  const isEditing = Boolean(memory);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<string>("GENERAL");
  const [importance, setImportance] = useState<string>("MEDIUM");

  useEffect(() => {
    if (memory) {
      setTitle(memory.title);
      setContent(memory.content);
      setCategory(memory.category);
      setImportance(memory.importance);
    } else {
      setTitle("");
      setContent("");
      setCategory("GENERAL");
      setImportance("MEDIUM");
    }
  }, [memory, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    onSave({
      id: memory?.id,
      title: title.trim(),
      content: content.trim(),
      category,
      importance,
    });
  };

  const categoryOptions = MEMORY_CATEGORIES.filter((c) => c.id !== "ALL");

  return (
    <>
      <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 transition-opacity" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="w-full max-w-lg rounded-2xl bg-bg border border-border shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-bold text-text">
              {isEditing ? "Edit AI Memory" : "Add Memory Manually"}
            </h3>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-secondary hover:text-text hover:bg-bg-alt transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Implementation-first learner"
                required
                className="w-full px-3 py-2 rounded-xl bg-bg-alt border border-border text-xs text-text focus:outline-none focus:border-accent"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1">
                Memory Content / Description
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Describe the fact or learning preference..."
                rows={4}
                required
                className="w-full px-3 py-2 rounded-xl bg-bg-alt border border-border text-xs text-text focus:outline-none focus:border-accent resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-bg-alt border border-border text-xs text-text focus:outline-none focus:border-accent cursor-pointer"
                >
                  {categoryOptions.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Importance</label>
                <select
                  value={importance}
                  onChange={(e) => setImportance(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-bg-alt border border-border text-xs text-text focus:outline-none focus:border-accent cursor-pointer"
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl border border-border text-xs font-semibold text-text-secondary hover:text-text hover:bg-bg-alt transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || !title.trim() || !content.trim()}
                className="px-4 py-2 rounded-xl bg-accent text-white font-bold text-xs shadow-md hover:bg-accent/90 disabled:opacity-50 transition-all cursor-pointer flex items-center gap-1.5"
              >
                {isEditing ? <Save className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                {isEditing ? "Save Changes" : "Create Memory"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
