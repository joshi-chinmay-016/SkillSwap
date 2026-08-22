import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Compass, Layers, Clock } from "lucide-react";
import CodeBlock from "../common/CodeBlock";
import ToolCard from "./ToolCard";

interface MentorResponseCardProps {
  content: string;
  recommendedTopics?: string[];
  difficultyLevel?: string;
  toolUsed?: string | null;
  toolSuccess?: boolean | null;
  toolExecutionTime?: number | null;
  toolData?: Record<string, any> | null;
  onTopicClick?: (topic: string) => void;
}

export default function MentorResponseCard({
  content,
  recommendedTopics = [],
  difficultyLevel = "Intermediate",
  toolUsed,
  toolSuccess,
  toolExecutionTime,
  toolData,
  onTopicClick,
}: MentorResponseCardProps) {
  const getDifficultyBadge = (level: string) => {
    switch (level.toLowerCase()) {
      case "beginner":
        return "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20";
      case "advanced":
        return "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20";
      default:
        return "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20";
    }
  };

  return (
    <div className="space-y-3">
      {/* Tool Card (rendered when backend used an internal tool) */}
      {toolUsed && (
        <ToolCard
          toolUsed={toolUsed}
          toolSuccess={toolSuccess}
          toolExecutionTime={toolExecutionTime}
          toolData={toolData}
        />
      )}

      {/* Markdown Body */}
      <div className="text-sm sm:text-[15px] text-text prose prose-sm sm:prose-base max-w-none prose-headings:text-text prose-headings:font-bold prose-p:text-text prose-p:leading-relaxed prose-li:text-text prose-strong:text-text prose-ul:text-text prose-ol:text-text">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || "");
              const codeString = String(children).replace(/\n$/, "");

              // If it's a code block (multiline or has language tag or not inline)
              if (!inline && (match || codeString.includes("\n"))) {
                return (
                  <CodeBlock
                    code={codeString}
                    language={match ? match[1] : "code"}
                  />
                );
              }

              // Single inline code snippet badge with high contrast
              return (
                <code
                  className="font-mono text-[12px] font-semibold text-accent bg-accent/10 border border-accent/20 px-1.5 py-0.5 rounded shadow-2xs"
                  {...props}
                >
                  {children}
                </code>
              );
            },
            // Custom pre wrapper to ensure no double margin or background bleeding
            pre({ children }: any) {
              return <>{children}</>;
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>

      {/* Footer Meta: Difficulty & Recommended Topics */}
      <div className="pt-3 border-t border-border/60 flex flex-wrap items-center justify-between gap-2 text-xs">
        {/* Difficulty Badge */}
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-text-secondary" />
          <span className="text-text-secondary text-[11px]">Level:</span>
          <span className={`px-2 py-0.5 rounded-full border font-medium text-[11px] ${getDifficultyBadge(difficultyLevel)}`}>
            {difficultyLevel}
          </span>
        </div>

        {/* Recommended Topics */}
        {recommendedTopics && recommendedTopics.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <Compass className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
            <span className="text-text-secondary text-[11px]">Next:</span>
            {recommendedTopics.map((topic, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onTopicClick?.(`Explain ${topic}`)}
                className="px-2 py-0.5 rounded-md bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 text-[11px] font-medium transition-colors cursor-pointer"
              >
                {topic} →
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
