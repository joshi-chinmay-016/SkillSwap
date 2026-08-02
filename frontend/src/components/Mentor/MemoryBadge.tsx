// src/components/Mentor/MemoryBadge.tsx

import React from "react";
import { MessageSquare, Cpu, Calendar, BookOpen, MapPin, Wrench, User, AlertCircle, Bookmark, Star, Zap } from "lucide-react";

interface MemoryBadgeProps {
  type: "importance" | "source" | "category";
  value: string;
}

export default function MemoryBadge({ type, value }: MemoryBadgeProps) {
  if (type === "importance") {
    const valUpper = value.toUpperCase();
    let badgeStyle = "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20";
    let Icon = Bookmark;

    if (valUpper === "CRITICAL") {
      badgeStyle = "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20";
      Icon = Zap;
    } else if (valUpper === "HIGH") {
      badgeStyle = "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20";
      Icon = Star;
    } else if (valUpper === "MEDIUM") {
      badgeStyle = "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20";
      Icon = Bookmark;
    }

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wider border uppercase ${badgeStyle}`}>
        <Icon className="w-3 h-3" />
        {value}
      </span>
    );
  }

  if (type === "source") {
    let Icon = MessageSquare;
    if (value.includes("AI Context")) Icon = Cpu;
    else if (value.includes("Session")) Icon = Calendar;
    else if (value.includes("Summary")) Icon = BookOpen;
    else if (value.includes("Journey")) Icon = MapPin;
    else if (value.includes("Tool")) Icon = Wrench;
    else if (value.includes("Manual")) Icon = User;

    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-bg-alt text-text-secondary border border-border">
        <Icon className="w-3 h-3 text-accent" />
        {value}
      </span>
    );
  }

  // Category
  const categoryLabels: Record<string, string> = {
    LEARNING_STYLE: "Learning Style",
    LONG_TERM_GOAL: "Goal",
    STRONG_TOPIC: "Strong Topic",
    WEAK_TOPIC: "Weak Topic",
    LEARNING_PREFERENCE: "Preference",
    FREQUENT_TOPIC: "Frequent Topic",
    ACHIEVEMENT: "Achievement",
    PERSONAL_PREFERENCE: "Personal Preference",
    GENERAL: "General",
  };

  const label = categoryLabels[value] || value;

  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent/10 text-accent border border-accent/20">
      {label}
    </span>
  );
}
