import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Sparkles, FolderPlus, AlertCircle, ShieldCheck } from "lucide-react";
import CodeBlock from "../common/CodeBlock";

export default function AnswerCard({
  answer,
  insufficientContext,
  contextChunkCount,
  model,
  grounded,
}) {
  const navigate = useNavigate();

  if (insufficientContext) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-amber-500/10 border border-amber-500/30 rounded-2xl space-y-4"
      >
        <div className="flex items-center gap-2.5 text-amber-600 dark:text-amber-400 font-bold text-sm">
          <AlertCircle size={18} />
          <span>No Relevant Knowledge Found</span>
        </div>
        <p className="text-xs text-text-secondary leading-relaxed">
          I couldn't find relevant information in your indexed Knowledge Base to answer this question accurately. You can add relevant materials (PDFs, Markdown, text notes) to your Knowledge Library so your AI Mentor can ground its answers.
        </p>
        <div className="pt-1">
          <button
            type="button"
            onClick={() => navigate("/mentor/knowledge?tab=documents")}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-accent text-white text-xs font-semibold hover:bg-accent-hover transition-colors shadow-xs cursor-pointer"
          >
            <FolderPlus size={14} />
            <span>View & Add Knowledge</span>
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-bg border border-border rounded-2xl shadow-xl overflow-hidden transition-colors"
    >
      {/* Header */}
      <div className="px-6 py-4 bg-bg-alt/40 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-accent/15 text-accent flex items-center justify-center border border-accent/20">
            <Sparkles size={16} />
          </div>
          <span className="text-sm font-bold text-text">AI Grounded Answer</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-success/10 text-success border border-success/20">
            Grounded in {contextChunkCount} {contextChunkCount === 1 ? "chunk" : "chunks"}
          </span>
          {grounded === true && (
            <span
              title="Answer verified against retrieved Knowledge"
              className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
            >
              <ShieldCheck size={11} />
              Grounded
            </span>
          )}
        </div>

        {model && (
          <span className="text-[11px] font-mono text-text-secondary bg-bg-alt px-2 py-1 rounded-md border border-border">
            {model}
          </span>
        )}
      </div>

      {/* Answer Content Area */}
      <div className="p-6 text-sm text-text leading-relaxed font-sans max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || "");
              const codeString = String(children).replace(/\n$/, "");

              if (!inline && match) {
                return <CodeBlock code={codeString} language={match[1]} />;
              }

              if (!inline && codeString.includes("\n")) {
                return <CodeBlock code={codeString} language="text" />;
              }

              return (
                <code
                  className="px-1.5 py-0.5 rounded-md bg-bg-alt text-accent font-mono text-xs border border-border"
                  {...props}
                >
                  {children}
                </code>
              );
            },
            h1: ({ children }) => <h1 className="text-lg font-bold text-text mb-3 mt-4 border-b border-border pb-1">{children}</h1>,
            h2: ({ children }) => <h2 className="text-base font-bold text-text mb-2 mt-3">{children}</h2>,
            h3: ({ children }) => <h3 className="text-sm font-bold text-text mb-2 mt-2">{children}</h3>,
            p: ({ children }) => <p className="mb-3 leading-relaxed text-text">{children}</p>,
            ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
            li: ({ children }) => <li className="text-text">{children}</li>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-accent/60 pl-4 py-1 italic bg-accent/5 text-text-secondary my-3 rounded-r-lg">
                {children}
              </blockquote>
            ),
          }}
        >
          {answer}
        </ReactMarkdown>
      </div>
    </motion.div>
  );
}
