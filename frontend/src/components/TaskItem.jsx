import React from "react";
import { CheckCircle } from "lucide-react";

// Reusable component to display a single journey task
export default function TaskItem({ task }) {
  const { title, description, resources = [] } = task || {};

  return (
    <div className="flex items-start gap-2 p-2 border border-border/30 rounded-md bg-bg-alt/10 hover:bg-bg-alt/20 transition-colors">
      <div className="mt-1 flex-shrink-0">
        <CheckCircle className="text-success" size={16} />
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-sm text-text" title={title}>
          {title}
        </h4>
        {description && (
          <p className="text-xs text-text-secondary mt-0.5" title={description}>
            {description}
          </p>
        )}
        {resources.length > 0 && (
          <ul className="mt-1 list-disc list-inside text-xs text-text-secondary">
            {resources.map((res, idx) => (
              <li key={idx}>{res}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
