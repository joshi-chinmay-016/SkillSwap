import React, { useState } from "react";
import { Sparkles, Brain, BookOpen, AlertCircle } from "lucide-react";
import { useRAGQuery } from "../hooks/useRAGQuery";
import KnowledgePipelineVisual from "../components/rag/KnowledgePipelineVisual";
import RAGInput from "../components/rag/RAGInput";
import RAGLoadingState from "../components/rag/RAGLoadingState";
import RAGErrorState from "../components/rag/RAGErrorState";
import AnswerCard from "../components/rag/AnswerCard";
import SourceList from "../components/rag/SourceList";

export default function RAGQueryPage() {
  const [responseStyle, setResponseStyle] = useState("detailed");
  const [activeQuery, setActiveQuery] = useState("");

  const ragMutation = useRAGQuery();

  const handleQuerySubmit = (queryText) => {
    setActiveQuery(queryText);
    ragMutation.mutate({
      query: queryText,
      response_style: responseStyle,
    });
  };

  const handleReset = () => {
    setActiveQuery("");
    ragMutation.reset();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Decorative Architecture Visual */}
      <KnowledgePipelineVisual />

      {/* RAG Question Input */}
      <RAGInput
        onSubmit={handleQuerySubmit}
        isPending={ragMutation.isPending}
        onReset={handleReset}
        hasAnswer={Boolean(ragMutation.data)}
        responseStyle={responseStyle}
        setResponseStyle={setResponseStyle}
      />

      {/* Active Output State Rendering */}
      {ragMutation.isPending && <RAGLoadingState />}

      {ragMutation.isError && (
        <RAGErrorState
          error={ragMutation.error}
          onRetry={() => activeQuery && handleQuerySubmit(activeQuery)}
        />
      )}

      {ragMutation.data && (
        <div className="space-y-6 animate-fadeIn">
          <AnswerCard
            answer={ragMutation.data.answer}
            insufficientContext={ragMutation.data.insufficient_context}
            contextChunkCount={ragMutation.data.context_chunk_count}
            model={ragMutation.data.model}
          />

          {!ragMutation.data.insufficient_context && (
            <SourceList sources={ragMutation.data.sources} />
          )}
        </div>
      )}
    </div>
  );
}
