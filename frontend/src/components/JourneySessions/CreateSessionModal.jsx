import React, { useState, useEffect, useRef } from "react";
import Button from "../common/Button";
import { X, Sparkles, Loader2 } from "lucide-react";

/**
 * CreateSessionModal Component
 * Modal for creating a new Learning Session with title input and validation.
 */
export default function CreateSessionModal({ isOpen, onClose, onSubmit, isSubmitting }) {
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTitle("");
      setError("");
      // Auto-focus title input when modal opens
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmedTitle = title.trim();

    if (!trimmedTitle) {
      setError("Session title is required.");
      return;
    }

    if (trimmedTitle.length > 255) {
      setError("Title cannot exceed 255 characters.");
      return;
    }

    setError("");
    onSubmit({ title: trimmedTitle });
  };

  const handleKeyDown = (e) => {
    if (e.key === "Escape" && !isSubmitting) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200"
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className="w-full max-w-md bg-bg border border-border rounded-xl shadow-xl overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg-alt/50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-accent/10 text-accent rounded-lg">
              <Sparkles size={18} />
            </div>
            <h3 id="modal-title" className="text-base font-bold text-text">
              Create Learning Session
            </h3>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close modal"
            className="p-1 text-text-secondary hover:text-text hover:bg-bg-alt rounded-md transition-colors disabled:opacity-50"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label
              htmlFor="session-title-input"
              className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1.5"
            >
              Session Title <span className="text-danger">*</span>
            </label>
            <input
              id="session-title-input"
              ref={inputRef}
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (error) setError("");
              }}
              placeholder="e.g. Sliding Window Technique & Practice"
              maxLength={255}
              disabled={isSubmitting}
              className={`w-full px-3.5 py-2.5 bg-bg text-text text-sm rounded-lg border focus:outline-none transition-colors ${
                error
                  ? "border-danger focus:ring-1 focus:ring-danger"
                  : "border-border focus:border-accent focus:ring-1 focus:ring-accent"
              }`}
            />
            {error && (
              <p className="mt-1.5 text-xs text-danger font-medium flex items-center gap-1">
                {error}
              </p>
            )}
            <p className="mt-1 text-[11px] text-text-secondary">
              Give your session a descriptive title. You will be able to complete or archive it later.
            </p>
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-border/60">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={14} className="mr-1.5 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Session"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
