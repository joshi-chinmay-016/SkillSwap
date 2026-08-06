import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import DocumentCard from "./DocumentCard";
import DocumentListItem from "./DocumentListItem";

export default function DocumentGrid({
  documents = [],
  viewMode = "grid",
  onPreview,
  onRename,
  onDownload,
  onDelete,
  onRetry,
}) {
  const [hoveredDocId, setHoveredDocId] = useState(null);

  const isAnyHovered = hoveredDocId !== null;

  if (viewMode === "list") {
    return (
      <div className="flex flex-col gap-2.5">
        <AnimatePresence mode="popLayout">
          {documents.map((doc) => {
            const isHovered = hoveredDocId === doc.id;
            return (
              <div
                key={doc.id}
                onMouseEnter={() => setHoveredDocId(doc.id)}
                onMouseLeave={() => setHoveredDocId(null)}
                className={`transition-all duration-300 ${
                  isAnyHovered && !isHovered ? "opacity-40 blur-[1px] scale-[0.99]" : "opacity-100 scale-100 z-10"
                }`}
              >
                <DocumentListItem
                  document={doc}
                  onPreview={onPreview}
                  onRename={onRename}
                  onDownload={onDownload}
                  onDelete={onDelete}
                  onRetry={onRetry}
                />
              </div>
            );
          })}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <AnimatePresence mode="popLayout">
        {documents.map((doc) => {
          const isHovered = hoveredDocId === doc.id;
          return (
            <div
              key={doc.id}
              onMouseEnter={() => setHoveredDocId(doc.id)}
              onMouseLeave={() => setHoveredDocId(null)}
              className={`transition-all duration-300 ${
                isAnyHovered && !isHovered ? "opacity-40 blur-[1.5px] scale-[0.98]" : "opacity-100 scale-100 z-10"
              }`}
            >
              <DocumentCard
                document={doc}
                isHovered={isHovered}
                onPreview={onPreview}
                onRename={onRename}
                onDownload={onDownload}
                onDelete={onDelete}
                onRetry={onRetry}
              />
            </div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
