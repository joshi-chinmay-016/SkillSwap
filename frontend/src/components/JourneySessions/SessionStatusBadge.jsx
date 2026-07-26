import React from "react";
import { PlayCircle, CheckCircle2, Archive } from "lucide-react";

/**
 * SessionStatusBadge Component
 * Renders status badges for ACTIVE (Blue), COMPLETED (Green), and ARCHIVED (Gray).
 */
export default function SessionStatusBadge({ status, className = "" }) {
  const normalizedStatus = (status || "").toUpperCase();

  switch (normalizedStatus) {
    case "ACTIVE":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border bg-accent/10 text-accent border-accent/20 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          <PlayCircle size={12} className="shrink-0" />
          ACTIVE
        </span>
      );

    case "COMPLETED":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border bg-success/10 text-success border-success/20 ${className}`}
        >
          <CheckCircle2 size={12} className="shrink-0" />
          COMPLETED
        </span>
      );

    case "ARCHIVED":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border bg-border/40 text-text-secondary border-border/40 ${className}`}
        >
          <Archive size={12} className="shrink-0" />
          ARCHIVED
        </span>
      );

    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border bg-bg-alt text-text-secondary border-border ${className}`}
        >
          {status}
        </span>
      );
  }
}
