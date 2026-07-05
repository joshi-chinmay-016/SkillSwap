import React, { useState } from "react";

export default function Avatar({ src, alt = "", size = "md", className = "" }) {
  const [imageError, setImageError] = useState(false);

  // Helper to extract initials (up to 2 letters) from a name
  const getInitials = (name) => {
    if (!name) return "?";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
  };

  const sizes = {
    xs: "w-6 h-6 text-[10px]",
    sm: "w-8 h-8 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-12 h-12 text-base",
    xl: "w-16 h-16 text-xl",
    "2xl": "w-24 h-24 text-3xl",
  };

  const hasImage = src && !imageError;

  return (
    <div
      className={`relative inline-flex items-center justify-center rounded-full overflow-hidden select-none shrink-0 font-semibold ${
        sizes[size]
      } ${
        hasImage ? "bg-border" : "bg-gradient-to-br from-accent/70 to-accent text-white"
      } ${className}`}
    >
      {hasImage ? (
        <img
          src={src}
          alt={alt}
          onError={() => setImageError(true)}
          className="w-full h-full object-cover"
        />
      ) : (
        <span>{getInitials(alt)}</span>
      )}
    </div>
  );
}
