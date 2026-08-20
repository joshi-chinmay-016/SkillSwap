import React from "react";
import { motion } from "motion/react";

export default function Card({
  title,
  subtitle,
  children,
  footer,
  className = "",
  onClick,
  hoverable = false,
  glass = false,
  badge,
  ...props
}) {
  const isClickable = !!onClick || hoverable;

  const baseStyles = glass
    ? "rounded-2xl border border-glass-border bg-glass-bg backdrop-blur-md text-text overflow-hidden shadow-sm transition-all duration-200"
    : "rounded-2xl border border-card-border bg-card-bg text-text overflow-hidden shadow-xs hover:border-accent/40 transition-all duration-200";

  const hoverStyles = isClickable
    ? "hover:shadow-md hover:border-accent/40 cursor-pointer"
    : "";

  const containerStyles = `${baseStyles} ${hoverStyles} ${className}`;

  const content = (
    <div className="flex flex-col h-full">
      {(title || subtitle || badge) && (
        <div className="px-5 py-4 border-b border-border flex items-center justify-between gap-2">
          <div>
            {title && <h3 className="font-semibold text-base text-text tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-text-secondary mt-0.5">{subtitle}</p>}
          </div>
          {badge && <div>{badge}</div>}
        </div>
      )}
      <div className="px-5 py-4 flex-grow text-sm">{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-border bg-bg-alt/50 text-xs">
          {footer}
        </div>
      )}
    </div>
  );

  if (isClickable) {
    return (
      <motion.article
        onClick={onClick}
        whileHover={{ translateY: -3, scale: 1.005 }}
        whileTap={{ translateY: 0, scale: 0.995 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className={containerStyles}
        {...props}
      >
        {content}
      </motion.article>
    );
  }

  return (
    <article className={containerStyles} {...props}>
      {content}
    </article>
  );
}
