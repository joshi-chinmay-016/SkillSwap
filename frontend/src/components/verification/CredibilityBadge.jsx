import React from "react";
import { Shield, ShieldCheck, Award, CheckCircle2, AlertCircle } from "lucide-react";

export default function CredibilityBadge({ status = "CLAIMED", score = null, size = "md", showLabel = true }) {
  const normalizedStatus = (status || "CLAIMED").toUpperCase();

  const config = {
    CLAIMED: {
      label: "Claimed",
      bgColor: "bg-slate-100 dark:bg-slate-800",
      textColor: "text-slate-700 dark:text-slate-300",
      borderColor: "border-slate-300 dark:border-slate-700",
      icon: Shield,
      tooltip: "Skill self-claimed by user. Assessment available.",
    },
    ASSESSED: {
      label: "Assessed",
      bgColor: "bg-blue-50 dark:bg-blue-950/40",
      textColor: "text-blue-700 dark:text-blue-300",
      borderColor: "border-blue-300 dark:border-blue-800",
      icon: AlertCircle,
      tooltip: "Assessment completed. Evidence score recorded.",
    },
    VERIFIED: {
      label: "Verified",
      bgColor: "bg-emerald-50 dark:bg-emerald-950/40",
      textColor: "text-emerald-700 dark:text-emerald-300",
      borderColor: "border-emerald-300 dark:border-emerald-800",
      icon: CheckCircle2,
      tooltip: "Verified via successful assessment demonstration.",
    },
    TRUSTED: {
      label: "Trusted Mentor",
      bgColor: "bg-purple-50 dark:bg-purple-950/40",
      textColor: "text-purple-700 dark:text-purple-300",
      borderColor: "border-purple-300 dark:border-purple-800",
      icon: Award,
      tooltip: "Earned top credibility status via ratings and session history.",
    },
  };

  const current = config[normalizedStatus] || config.CLAIMED;
  const IconComponent = current.icon;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1",
    md: "px-2.5 py-1 text-xs font-medium gap-1.5",
    lg: "px-3 py-1.5 text-sm font-semibold gap-2",
  }[size] || "px-2.5 py-1 text-xs gap-1.5";

  const iconSizes = {
    sm: 12,
    md: 14,
    lg: 16,
  }[size] || 14;

  return (
    <span
      className={`inline-flex items-center rounded-full border ${current.bgColor} ${current.textColor} ${current.borderColor} ${sizeClasses} transition-colors`}
      title={current.tooltip}
    >
      <IconComponent size={iconSizes} className="shrink-0" />
      {showLabel && <span>{current.label}</span>}
      {score !== null && score !== undefined && (
        <span className="opacity-80 font-mono text-[0.85em]">
          ({Math.round(score)}%)
        </span>
      )}
    </span>
  );
}
