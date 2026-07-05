import React from "react";
import { motion } from "motion/react";

export default function Skeleton({
  variant = "rectangular",
  width,
  height,
  className = "",
  animated = true,
  ...props
}) {
  const baseStyles = "bg-border/40";
  
  const variantStyles = {
    rectangular: "rounded-md",
    circular: "rounded-full",
    text: "rounded-sm",
  };

  const widthStyle = width ? { width } : {};
  const heightStyle = height ? { height } : {};

  if (animated) {
    return (
      <motion.div
        initial={{ opacity: 0.5 }}
        animate={{ opacity: 1 }}
        transition={{
          duration: 1,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut",
        }}
        className={`
          ${baseStyles}
          ${variantStyles[variant]}
          ${className}
        `}
        style={widthStyle || heightStyle ? { ...widthStyle, ...heightStyle } : undefined}
        {...props}
      />
    );
  }

  return (
    <div
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${className}
      `}
      style={widthStyle || heightStyle ? { ...widthStyle, ...heightStyle } : undefined}
      {...props}
    />
  );
}

// Preset skeleton components for common patterns
export function SkeletonCard() {
  return (
    <div className="rounded-lg border border-border bg-bg-alt p-4 space-y-3">
      <Skeleton variant="text" width="60%" height="20px" />
      <Skeleton variant="text" width="90%" height="14px" />
      <Skeleton variant="text" width="75%" height="14px" />
      <div className="flex gap-2 pt-2">
        <Skeleton variant="rectangular" width="80px" height="32px" />
        <Skeleton variant="rectangular" width="80px" height="32px" />
      </div>
    </div>
  );
}

export function SkeletonAvatar({ size = "md" }) {
  const sizes = {
    sm: "w-8 h-8",
    md: "w-10 h-10",
    lg: "w-12 h-12",
    xl: "w-16 h-16",
  };

  return (
    <Skeleton variant="circular" className={sizes[size]} />
  );
}

export function SkeletonTable({ rows = 3, columns = 4 }) {
  return (
    <div className="space-y-3">
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} variant="text" width="100px" height="16px" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={colIndex}
              variant="text"
              width={colIndex === 0 ? "120px" : "80px"}
              height="14px"
            />
          ))}
        </div>
      ))}
    </div>
  );
}