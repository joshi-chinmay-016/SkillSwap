// src/components/Mentor/ToolCard.tsx

import React from "react";
import ToolBadge from "./ToolBadge";
import ProgressCard from "./ProgressCard";
import AnalyticsCard from "./AnalyticsCard";
import JourneyCard from "./JourneyCard";
import SummaryCard from "./SummaryCard";

interface ToolCardProps {
  toolUsed?: string | null;
  toolSuccess?: boolean | null;
  toolExecutionTime?: number | null;
  toolData?: Record<string, any> | null;
}

export default function ToolCard({
  toolUsed,
  toolSuccess,
  toolExecutionTime,
  toolData,
}: ToolCardProps) {
  if (!toolUsed) return null;

  const isSuccess = toolSuccess !== false;

  const renderStructuredData = () => {
    if (!isSuccess || !toolData) return null;

    switch (toolUsed) {
      case "LearningProgressTool":
        return <ProgressCard data={toolData} />;
      case "LearningAnalyticsTool":
        return <AnalyticsCard data={toolData} />;
      case "JourneyTool":
        return <JourneyCard data={toolData} />;
      case "SessionSummaryTool":
        return <SummaryCard data={toolData} />;
      case "AIContextTool":
        // AIContextTool data is displayed inline or via profile cards
        if (toolData.strong_topics || toolData.weak_topics) {
          return (
            <div className="p-2.5 rounded-xl bg-bg border border-border/80 text-xs space-y-1.5 my-2">
              {toolData.strong_topics?.length > 0 && (
                <p className="text-text-secondary">
                  <strong className="text-emerald-600 dark:text-emerald-400">Mastered:</strong>{" "}
                  {toolData.strong_topics.join(", ")}
                </p>
              )}
              {toolData.weak_topics?.length > 0 && (
                <p className="text-text-secondary">
                  <strong className="text-amber-600 dark:text-amber-400">Target Gaps:</strong>{" "}
                  {toolData.weak_topics.join(", ")}
                </p>
              )}
            </div>
          );
        }
        return null;
      default:
        return null;
    }
  };

  return (
    <div className="mb-3 p-3 rounded-2xl bg-accent/5 border border-accent/15 space-y-2 text-xs transition-all shadow-2xs">
      {/* Header Badge */}
      <ToolBadge
        toolName={toolUsed}
        toolSuccess={toolSuccess}
        executionTimeMs={toolExecutionTime}
      />

      {/* Description */}
      {isSuccess ? (
        <p className="text-[11px] text-text-secondary font-medium pl-0.5">
          Based on your real learning activity on SkillSwap.
        </p>
      ) : (
        <p className="text-[11px] text-amber-600 dark:text-amber-400 font-medium pl-0.5">
          Unable to retrieve learning data. AI Mentor responded using general knowledge.
        </p>
      )}

      {/* Structured Tool Result Card */}
      {renderStructuredData()}
    </div>
  );
}
