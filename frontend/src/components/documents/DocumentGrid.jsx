import React from "react";
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
}) {
  if (viewMode === "list") {
    return (
      <div className="flex flex-col gap-2.5">
        <AnimatePresence mode="popLayout">
          {documents.map((doc) => (
            <DocumentListItem
              key={doc.id}
              document={doc}
              onPreview={onPreview}
              onRename={onRename}
              onDownload={onDownload}
              onDelete={onDelete}
            />
          ))}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <AnimatePresence mode="popLayout">
        {documents.map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            onPreview={onPreview}
            onRename={onRename}
            onDownload={onDownload}
            onDelete={onDelete}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
