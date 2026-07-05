import React from "react";
import Avatar from "./Avatar";

export default function AvatarGroup({ avatars = [], max = 3, size = "md", className = "" }) {
  const visibleAvatars = avatars.slice(0, max);
  const remainingCount = Math.max(0, avatars.length - max);

  const sizeClasses = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base",
  };

  return (
    <div className={`flex items-center ${className}`}>
      <div className="flex -space-x-2">
        {visibleAvatars.map((avatar, index) => (
          <div
            key={index}
            className={`rounded-full border-2 border-bg ${sizeClasses[size]}`}
            style={{ zIndex: visibleAvatars.length - index }}
          >
            <Avatar
              src={avatar.src}
              alt={avatar.alt || `User ${index + 1}`}
              size={size}
              className="rounded-full"
            />
          </div>
        ))}
        {remainingCount > 0 && (
          <div
            className={`rounded-full border-2 border-bg bg-bg-alt text-text-secondary font-semibold flex items-center justify-center ${sizeClasses[size]}`}
            style={{ zIndex: 0 }}
          >
            +{remainingCount}
          </div>
        )}
      </div>
    </div>
  );
}
