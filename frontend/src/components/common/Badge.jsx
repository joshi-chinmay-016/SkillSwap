import React from "react";
import { motion } from "motion/react";
import { X } from "lucide-react";

export default function Badge({
  children,
  variant = "default",
  size = "md",
  removable = false,
  onRemove,
  className = "",
  ...props
}) {
  const variants = {
    default: "bg-bg-alt text-text border-border",
    primary: "bg-accent/10 text-accent border-accent/20",
    success: "bg-green-500/10 text-green-600 border-green-500/20",
    warning: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
    danger: "bg-danger/10 text-danger border-danger/20",
    outline: "bg-transparent text-text border-border",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-[10px] gap-1",
    md: "px-2.5 py-1 text-xs gap-1.5",
    lg: "px-3 py-1.5 text-sm gap-2",
  };

  const baseStyles = "inline-flex items-center rounded-full border font-medium transition-colors";
  const currentStyles = `${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`;

  const handleRemove = (e) => {
    e.stopPropagation();
    onRemove?.();
  };

  return (
    <motion.span
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.8, opacity: 0 }}
      transition={{ duration: 0.1 }}
      className={currentStyles}
      {...props}
    >
      {children}
      {removable && (
        <button
          type="button"
          onClick={handleRemove}
          className="ml-0.5 rounded-full hover:bg-black/10 p-0.5 cursor-pointer transition-colors"
          aria-label="Remove badge"
        >
          <X size={size === "sm" ? 10 : size === "md" ? 12 : 14} />
        </button>
      )}
    </motion.span>
  );
}