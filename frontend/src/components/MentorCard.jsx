import React from "react";
import Card from "./common/Card";
import Avatar from "./common/Avatar";
import { Star, Calendar, ArrowRight } from "lucide-react";

export default function MentorCard({ mentor, onClick }) {
  const { mentor_id, mentor_name, average_rating, completed_sessions } = mentor;

  return (
    <Card
      onClick={onClick}
      hoverable={true}
      className="flex flex-col h-full bg-bg border border-border text-left"
    >
      <div className="flex items-start gap-4">
        <Avatar
          src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${mentor_name}`}
          alt={mentor_name}
          size="lg"
        />
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-sm text-text truncate leading-snug">
            {mentor_name}
          </h3>
          
          {/* Rating */}
          <div className="flex items-center gap-1 mt-1 text-xs">
            <div className="flex items-center text-yellow-500">
              <Star size={14} fill="currentColor" />
            </div>
            <span className="font-semibold text-text">
              {average_rating > 0 ? average_rating.toFixed(1) : "New"}
            </span>
            <span className="text-text-secondary">•</span>
            <span className="text-text-secondary flex items-center gap-1">
              <Calendar size={12} /> {completed_sessions} completed sessions
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3.5 border-t border-border flex items-center justify-between text-xs font-semibold text-accent group cursor-pointer">
        <span>View Profile & Book</span>
        <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
      </div>
    </Card>
  );
}
