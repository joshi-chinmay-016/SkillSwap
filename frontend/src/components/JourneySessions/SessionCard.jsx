import React from "react";
import { useNavigate } from "react-router-dom";
import SessionStatusBadge from "./SessionStatusBadge";
import Button from "../common/Button";
import { Play, CheckCircle, Eye, Archive, Clock, Calendar } from "lucide-react";

/**
 * Utility to format relative or local date strings
 */
const formatDate = (dateString) => {
  if (!dateString) return null;
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString;

  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} mins ago`;
  if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

/**
 * SessionCard Component
 * Displays session details, status badge, timestamps, and action buttons.
 */
export default function SessionCard({ session, onComplete, onArchive }) {
  const navigate = useNavigate();

  const handleContinue = () => {
    navigate(`/learning-sessions/${session.id}`);
  };

  const handleView = () => {
    navigate(`/learning-sessions/${session.id}`);
  };

  const status = (session.status || "").toUpperCase();

  return (
    <div className="border border-border rounded-xl bg-bg p-5 hover:border-accent/40 transition-all duration-200 shadow-xs flex flex-col justify-between gap-4">
      {/* Top Header & Status */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-text text-sm leading-snug truncate" title={session.title}>
            {session.title}
          </h4>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-secondary mt-1.5">
            <span className="flex items-center gap-1" title="Started time">
              <Clock size={12} className="text-accent shrink-0" />
              Started {formatDate(session.started_at)}
            </span>

            {session.ended_at && (
              <span className="flex items-center gap-1 text-success font-medium" title="Completed time">
                <CheckCircle size={12} className="shrink-0" />
                Ended {formatDate(session.ended_at)}
              </span>
            )}
          </div>
        </div>

        <SessionStatusBadge status={status} className="shrink-0" />
      </div>

      {/* Footer Info & Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-border/60 text-xs">
        <span className="text-[11px] text-text-secondary flex items-center gap-1">
          <Calendar size={12} />
          Created {formatDate(session.created_at)}
        </span>

        <div className="flex items-center gap-2">
          {status === "ACTIVE" && (
            <>
              <Button
                variant="outline"
                size="xs"
                onClick={() => onArchive(session)}
                title="Archive session"
                className="text-text-secondary hover:text-danger hover:border-danger/30"
              >
                <Archive size={12} className="mr-1" />
                Archive
              </Button>

              <Button
                variant="outline"
                size="xs"
                onClick={() => onComplete(session)}
                className="text-success border-success/30 hover:bg-success/10"
              >
                <CheckCircle size={12} className="mr-1" />
                Complete
              </Button>

              <Button
                variant="primary"
                size="xs"
                onClick={handleContinue}
              >
                <Play size={12} className="mr-1 fill-current" />
                Continue
              </Button>
            </>
          )}

          {status === "COMPLETED" && (
            <>
              <Button
                variant="outline"
                size="xs"
                onClick={() => onArchive(session)}
                className="text-text-secondary hover:text-danger hover:border-danger/30"
              >
                <Archive size={12} className="mr-1" />
                Archive
              </Button>

              <Button
                variant="outline"
                size="xs"
                onClick={handleView}
              >
                <Eye size={12} className="mr-1" />
                View
              </Button>
            </>
          )}

          {status === "ARCHIVED" && (
            <Button
              variant="outline"
              size="xs"
              onClick={handleView}
            >
              <Eye size={12} className="mr-1" />
              View
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
