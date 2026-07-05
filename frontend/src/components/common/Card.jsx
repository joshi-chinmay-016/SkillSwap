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
  ...props
}) {
  const isClickable = !!onClick || hoverable;

  const baseStyles = "rounded-lg border border-border bg-bg-alt text-text overflow-hidden shadow-sm transition-shadow";
  const hoverStyles = isClickable ? "hover:shadow-md hover:border-accent/40 cursor-pointer" : "";

  const containerStyles = `${baseStyles} ${hoverStyles} ${className}`;

  const content = (
    <div className="flex flex-col h-full">
      {(title || subtitle) && (
        <div className="px-5 py-4 border-b border-border bg-bg flex flex-col gap-0.5">
          {title && <h3 className="font-semibold text-base text-text">{title}</h3>}
          {subtitle && <p className="text-xs text-text-secondary">{subtitle}</p>}
        </div>
      )}
      <div className="px-5 py-4 flex-grow text-sm">{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-border bg-bg text-xs">
          {footer}
        </div>
      )}
    </div>
  );

  if (isClickable) {
    return (
      <motion.article
        onClick={onClick}
        whileHover={{ translateY: -3 }}
        transition={{ duration: 0.15, ease: "easeOut" }}
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
