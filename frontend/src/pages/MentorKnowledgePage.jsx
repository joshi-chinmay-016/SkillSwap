import React, { useState } from "react";
import { useSearchParams } from "react-router-dom";
import MentorNavTabs from "../components/Mentor/MentorNavTabs";
import RAGQueryPage from "./RAGQueryPage";
import DocumentLibraryPage from "./DocumentLibraryPage";
import { Sparkles, FolderOpen, BookOpen } from "lucide-react";

export default function MentorKnowledgePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") === "documents" ? "documents" : "rag";

  const handleTabChange = (tab) => {
    if (tab === "documents") {
      setSearchParams({ tab: "documents" });
    } else {
      setSearchParams({});
    }
  };

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-6.5rem)]">
      {/* Outer Card Container */}
      <div className="flex-1 flex flex-col bg-bg border border-border rounded-2xl shadow-sm overflow-hidden">
        {/* Mentor Workspace Navigation Bar */}
        <MentorNavTabs />

        {/* Sub-Header & Mode Switcher */}
        <div className="px-6 py-4 bg-bg-alt/30 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
          <div>
            <h1 className="text-lg font-bold text-text flex items-center gap-2">
              <BookOpen size={18} className="text-accent" />
              <span>AI Mentor Knowledge Hub</span>
            </h1>
            <p className="text-xs text-text-secondary mt-0.5">
              Knowledge material uploaded here is indexed into FAISS vectors and used by AI Mentor to synthesize grounded answers.
            </p>
          </div>

          <div className="flex items-center gap-1 bg-bg p-1 rounded-xl border border-border shrink-0 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => handleTabChange("rag")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "rag"
                  ? "bg-accent text-white shadow-xs"
                  : "text-text-secondary hover:text-text hover:bg-bg-alt"
              }`}
            >
              <Sparkles size={13} />
              <span>Grounded Assistant</span>
            </button>

            <button
              type="button"
              onClick={() => handleTabChange("documents")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "documents"
                  ? "bg-accent text-white shadow-xs"
                  : "text-text-secondary hover:text-text hover:bg-bg-alt"
              }`}
            >
              <FolderOpen size={13} />
              <span>Document Library & FAISS Indexer</span>
            </button>
          </div>
        </div>

        {/* Workspace Content View */}
        <div className="flex-1 p-6 overflow-y-auto">
          {activeTab === "rag" ? (
            <RAGQueryPage />
          ) : (
            <DocumentLibraryPage />
          )}
        </div>
      </div>
    </div>
  );
}
