import React from "react";
import { motion } from "motion/react";
import Avatar from "./common/Avatar";
import CredibilityBadge from "./verification/CredibilityBadge";
import { PushPin } from "./common/PinnedCard";
import { Star, Calendar, ArrowRight, BookOpen, Sparkles, CheckCircle2 } from "lucide-react";

export default function MentorCard({
  mentor,
  onClick,
  pinColor = "red",
  sway = "left", // 'left', 'right', or 'none'
  index,
}) {
  const {
    id,
    mentor_id,
    name,
    mentor_name,
    avatar_url,
    department,
    year,
    average_rating = 0,
    rating = 0,
    completed_sessions = 0,
    verification_status = "CLAIMED",
    matched_skills = [],
    skills = [],
  } = mentor;

  const displayName = mentor_name || name || "Peer Mentor";
  const displayRating = average_rating || rating || 0;
  const displaySkills =
    matched_skills.length > 0
      ? matched_skills
      : skills.map((s) => (typeof s === "string" ? s : s.name));

  // Determine sway direction based on prop or index
  const activeSway =
    sway !== undefined && sway !== "none"
      ? sway
      : index !== undefined
      ? index % 2 === 0
        ? "left"
        : "right"
      : "left";

  const swayClass =
    activeSway === "left"
      ? "animate-sway-left"
      : activeSway === "right"
      ? "animate-sway-right"
      : "";

  return (
    <div style={{ perspective: 1000 }} className={`relative group ${swayClass}`}>
      {/* 3D Pushpin on top */}
      <PushPin color={pinColor} className="-top-3" />

      <div
        onClick={onClick}
        className="flex flex-col justify-between h-full bg-card-bg border border-card-border group-hover:border-accent/60 rounded-2xl p-5 shadow-sm group-hover:shadow-xl group-hover:scale-[1.02] transition-all duration-300 cursor-pointer text-left relative overflow-visible"
      >
        <div className="space-y-4 pt-1">
          {/* Top Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <Avatar
                src={
                  avatar_url ||
                  `https://api.dicebear.com/7.x/adventurer/svg?seed=${displayName}`
                }
                alt={displayName}
                size="lg"
                className="ring-2 ring-accent/25 shrink-0 group-hover:scale-105 transition-transform duration-200"
              />
              <div className="min-w-0 flex-1">
                <h3 className="font-bold text-sm text-text truncate group-hover:text-accent transition-colors">
                  {displayName}
                </h3>
                <p className="text-xs text-text-secondary truncate mt-0.5 font-handwriting text-base text-rose-500 font-bold">
                  {department ? `${department} • Year ${year || 1}` : "Verified Classmate"}
                </p>
              </div>
            </div>
            <CredibilityBadge status={verification_status} size="sm" />
          </div>

          {/* Rating & Sessions Stats Bar */}
          <div className="flex items-center gap-3 text-xs bg-bg-alt/70 p-2.5 rounded-xl border border-border/80">
            <div className="flex items-center gap-1 font-bold text-amber-500">
              <Star size={14} className="fill-amber-500" />
              <span className="text-text">
                {displayRating > 0 ? Number(displayRating).toFixed(1) : "New"}
              </span>
            </div>
            <span className="text-border">•</span>
            <div className="flex items-center gap-1 text-text-secondary font-medium">
              <Calendar size={13} className="text-accent shrink-0" />
              <span>
                {completed_sessions} session{completed_sessions === 1 ? "" : "s"}
              </span>
            </div>
          </div>

          {/* Skills Chips with Marker Styling */}
          {displaySkills.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Teaches & Exchanges:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {displaySkills.slice(0, 4).map((skillName, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-yellow-100 dark:bg-yellow-950/60 text-amber-900 dark:text-amber-300 border border-yellow-300 dark:border-yellow-700 shadow-2xs"
                  >
                    {skillName}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer CTA */}
        <div className="mt-4 pt-3 border-t border-border/80 flex items-center justify-between text-xs font-bold text-accent group-hover:text-accent-hover transition-colors">
          <span className="font-handwriting text-base font-bold text-accent">
            Schedule 1-on-1 Swap
          </span>
          <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
        </div>
      </div>
    </div>
  );
}
