// src/components/Mentor/ToolBadge.tsx

import React from "react";
import { Wrench, CheckCircle2, AlertCircle } from "lucide-react";

interface ToolBadgeProps {
  toolName?: string | null;
  toolSuccess?: boolean | null;
  executionTimeMs?: number | null;
}

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  LearningProgressTool: "Learning Progress",
  SessionSummaryTool: "Session Summary",
  JourneyTool: "Journey",
  LearningAnalyticsTool: "Analytics",
  AIContextTool: "AI Profile",
};

export function formatToolName(raw?: string | null): string {
  if (!raw) return "Internal Tool";
  if (TOOL_DISPLAY_NAMES[raw]) return TOOL_DISPLAY_NAMES[raw];
  return raw.replace(/Tool$/, "").replace(/([A-Z])/g, " $1").trim();
}

export default function ToolBadge({
  toolName,
  toolSuccess,
  executionTimeMs,
}: ToolBadgeProps) {
  if (!toolName) return null;

  const friendlyName = formatToolName(toolName);
  const isSuccess = toolSuccess !== false;

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {/* Tool Identifier Badge */}
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-accent/10 border border-accent/20 text-accent font-medium text-[11px] shadow-2xs">
        <Wrench className="w-3.5 h-3.5" />
        <span>Used {friendlyName}</span>
      </span>

      {/* Execution Status Badge */}
      {isSuccess ? (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-medium text-[11px]">
          <CheckCircle2 className="w-3 h-3" />
          <span>Verified using your SkillSwap data</span>
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 font-medium text-[11px]">
          <AlertCircle className="w-3 h-3" />
          <span>Using general knowledge</span>
        </span>
      )}

      {/* Execution Time Badge */}
      {executionTimeMs != null && executionTimeMs > 0 && (
        <span className="text-[10px] text-text-secondary font-mono opacity-80">
          ({executionTimeMs}ms)
        </span>
      )}
    </div>
  );
}
