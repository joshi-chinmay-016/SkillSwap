// src/components/common/CodeBlock.tsx

import React, { useState, useMemo } from "react";
import { Copy, Check, Code as CodeIcon } from "lucide-react";

interface CodeBlockProps {
  code: string;
  language?: string;
}

/**
 * Lightweight regex-based syntax highlighter for Python, JS/TS, C++, Java, Go, SQL.
 * Provides GitHub Dark / VSCode style colors with maximum contrast in both light & dark modes.
 */
function highlightCode(code: string, language: string = ""): React.ReactNode[] {
  const lines = code.split("\n");

  const lang = language.toLowerCase().trim();

  // Pattern definitions
  const kwRegex = /\b(def|class|import|from|return|if|elif|else|while|for|in|try|except|finally|raise|with|as|pass|break|continue|lambda|async|await|const|let|var|function|type|interface|export|default|public|private|protected|static|final|void|int|float|double|bool|boolean|string|struct|auto|namespace|using|select|from|where|join|insert|update|delete|group|by|order|limit|CREATE|TABLE|SELECT|FROM|WHERE)\b/g;
  const constRegex = /\b(True|False|None|null|undefined|self|this|true|false)\b/g;
  const numRegex = /\b(\d+(\.\d+)?)\b/g;
  const strRegex = /("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*'|`[^`\\]*(?:\\.[^`\\]*)*`)/g;
  const commentRegex = /(#.*|\/\/.*|\/\*[\s\S]*?\*\/)/g;
  const fnRegex = /\b([a-zA-Z_]\w*)(?=\()/g;

  return lines.map((line, lineIdx) => {
    if (!line.trim()) {
      return <div key={lineIdx} className="h-5" />;
    }

    // Tokenize line
    let tokens: { text: string; type: string; index: number }[] = [];

    // Helper to add tokens
    const matchAll = (regex: RegExp, type: string) => {
      let match;
      const re = new RegExp(regex.source, regex.flags);
      while ((match = re.exec(line)) !== null) {
        tokens.push({ text: match[0], type, index: match.index });
      }
    };

    matchAll(commentRegex, "comment");
    matchAll(strRegex, "string");
    matchAll(kwRegex, "keyword");
    matchAll(constRegex, "constant");
    matchAll(numRegex, "number");
    matchAll(fnRegex, "function");

    // Sort tokens by index
    tokens.sort((a, b) => a.index - b.index);

    // Filter out overlapping tokens (first token wins, comments override all)
    const filteredTokens: typeof tokens = [];
    let lastEnd = 0;

    for (const token of tokens) {
      if (token.index >= lastEnd) {
        // Check if comment started earlier
        const commentToken = tokens.find(t => t.type === "comment" && t.index <= token.index && (t.index + t.text.length) > token.index);
        if (commentToken && commentToken !== token) {
          continue;
        }
        filteredTokens.push(token);
        lastEnd = token.index + token.text.length;
      }
    }

    // Render line segments
    const lineElements: React.ReactNode[] = [];
    let currentIndex = 0;

    filteredTokens.forEach((token, tokenIdx) => {
      if (token.index > currentIndex) {
        lineElements.push(
          <span key={`plain-${currentIndex}`}>
            {line.slice(currentIndex, token.index)}
          </span>
        );
      }

      let styleClass = "text-[#c9d1d9]";
      if (token.type === "keyword") styleClass = "text-[#ff7b72] font-semibold"; // Red/Pink
      else if (token.type === "constant") styleClass = "text-[#79c0ff] font-semibold"; // Sky Blue
      else if (token.type === "string") styleClass = "text-[#a5d6ff]"; // Light Cyan
      else if (token.type === "number") styleClass = "text-[#79c0ff]"; // Light Blue
      else if (token.type === "comment") styleClass = "text-[#8b949e] italic"; // Slate Gray
      else if (token.type === "function") styleClass = "text-[#d2a8ff]"; // Purple

      lineElements.push(
        <span key={`token-${tokenIdx}`} className={styleClass}>
          {token.text}
        </span>
      );

      currentIndex = token.index + token.text.length;
    });

    if (currentIndex < line.length) {
      lineElements.push(
        <span key={`plain-end`}>
          {line.slice(currentIndex)}
        </span>
      );
    }

    return (
      <div key={lineIdx} className="table-row">
        <span className="table-cell text-right pr-4 select-none text-[#484f58] font-mono text-[11px] w-8">
          {lineIdx + 1}
        </span>
        <span className="table-cell whitespace-pre font-mono text-xs leading-relaxed text-[#c9d1d9]">
          {lineElements}
        </span>
      </div>
    );
  });
}

export default function CodeBlock({ code, language = "code" }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const cleanCode = useMemo(() => code.replace(/\n$/, ""), [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const highlightedLines = useMemo(
    () => highlightCode(cleanCode, language),
    [cleanCode, language]
  );

  return (
    <div className="my-4 rounded-xl overflow-hidden border border-[#30363d] bg-[#0d1117] shadow-lg text-[#c9d1d9] font-mono text-xs max-w-full">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#161b22] border-b border-[#30363d] text-xs">
        <div className="flex items-center gap-2 text-[#8b949e] font-sans text-[11px] font-medium">
          <CodeIcon className="w-3.5 h-3.5 text-[#58a6ff]" />
          <span className="uppercase tracking-wider font-semibold text-[#c9d1d9]">
            {language || "CODE"}
          </span>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] hover:text-white transition-all text-xs font-sans font-medium cursor-pointer border border-[#30363d]"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-[#8b949e]" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Container */}
      <div className="p-4 overflow-x-auto bg-[#0d1117] selection:bg-[#1f6feb] selection:text-white">
        <div className="table w-full border-collapse">
          {highlightedLines}
        </div>
      </div>
    </div>
  );
}
