import React from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import { Sparkles, PlusCircle } from "lucide-react";

/**
 * EmptySessions Component
 * Displays empty state when no sessions exist for a journey.
 */
export default function EmptySessions({ onCreateClick }) {
  return (
    <Card className="text-center py-10 px-6 border-dashed border-border/80 bg-bg-alt/30">
      <div className="flex flex-col items-center max-w-sm mx-auto">
        <div className="p-3.5 bg-accent/10 text-accent rounded-full mb-4 shadow-xs">
          <Sparkles size={28} />
        </div>
        
        <h3 className="text-base font-bold text-text">
          No learning sessions yet
        </h3>
        
        <p className="text-xs text-text-secondary mt-1.5 leading-relaxed">
          Start your first AI learning session for this journey to begin interactive mentoring, track activity, and earn achievements.
        </p>

        <div className="mt-5">
          <Button
            variant="primary"
            size="sm"
            onClick={onCreateClick}
            className="shadow-xs hover:shadow-md transition-all"
          >
            <PlusCircle size={16} className="mr-1.5" />
            Create Session
          </Button>
        </div>
      </div>
    </Card>
  );
}
