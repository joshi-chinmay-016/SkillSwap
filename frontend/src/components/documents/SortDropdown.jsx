import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ArrowUpDown, Check } from "lucide-react";

const SORT_OPTIONS = [
  { id: "newest", label: "Newest First" },
  { id: "oldest", label: "Oldest First" },
  { id: "ready_first", label: "Ready First" },
  { id: "parsing_first", label: "Parsing First" },
  { id: "name", label: "Name (A-Z)" },
];

export default function SortDropdown({ selectedSort, onSelectSort }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const activeOption = SORT_OPTIONS.find((o) => o.id === selectedSort) || SORT_OPTIONS[0];

  return (
    <div ref={dropdownRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-surface/80 border border-border/80 text-xs font-semibold text-text hover:bg-bg cursor-pointer transition-colors"
      >
        <ArrowUpDown size={14} className="text-text-secondary" />
        <span>{activeOption.label}</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-48 rounded-xl border border-border bg-surface/95 backdrop-blur-xl shadow-xl py-1 z-30 text-xs"
          >
            <div className="px-3 py-1.5 border-b border-border/60 text-[10px] font-bold text-text-secondary uppercase tracking-wider">
              Sort By
            </div>
            {SORT_OPTIONS.map((option) => (
              <button
                key={option.id}
                type="button"
                onClick={() => {
                  onSelectSort(option.id);
                  setIsOpen(false);
                }}
                className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-bg-alt text-text font-medium transition-colors cursor-pointer"
              >
                <span>{option.label}</span>
                {selectedSort === option.id && <Check size={14} className="text-primary" />}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
