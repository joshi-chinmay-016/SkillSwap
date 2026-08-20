import React from "react";
import { motion } from "motion/react";
import { Loader2 } from "lucide-react";

export default function Button({
  children,
  onClick,
  type = "button",
  variant = "primary",
  size = "md",
  disabled = false,
  isLoading = false,
  loading,
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  className = "",
  ...props
}) {
  const actualLoading = loading !== undefined ? loading : isLoading;

  const baseStyles =
    "relative inline-flex items-center justify-center font-medium select-none transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none cursor-pointer overflow-hidden";

  const variants = {
    primary:
      "bg-accent text-white hover:bg-accent-hover active:bg-accent-hover shadow-sm hover:shadow-glow border border-accent/20",
    secondary:
      "bg-surface-elevated text-text border border-border hover:border-accent/40 hover:bg-bg-alt shadow-xs",
    outline:
      "bg-transparent text-text border border-border hover:border-accent/50 hover:bg-accent-light/30",
    ghost:
      "bg-transparent text-text hover:bg-bg-alt hover:text-accent active:bg-border/40",
    danger:
      "bg-danger text-white hover:bg-red-600 active:bg-red-700 shadow-sm focus-visible:ring-danger border border-danger/20",
    glow:
      "bg-gradient-to-r from-accent to-purple-600 text-white shadow-glow hover:shadow-glow-lg border border-white/20",
  };

  const sizes = {
    xs: "px-2.5 py-1 text-[11px] rounded-md gap-1 font-semibold",
    sm: "px-3.5 py-1.5 text-xs rounded-lg gap-1.5 font-medium",
    md: "px-4.5 py-2 text-sm rounded-xl gap-2 font-medium",
    lg: "px-6 py-3 text-base rounded-xl gap-2.5 font-semibold",
  };

  const currentStyles = `${baseStyles} ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`;

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled || actualLoading}
      whileHover={disabled || actualLoading ? {} : { scale: 1.02, translateY: -1 }}
      whileTap={disabled || actualLoading ? {} : { scale: 0.98, translateY: 0 }}
      transition={{ duration: 0.15, ease: "easeOut" }}
      className={currentStyles}
      {...props}
    >
      {actualLoading ? (
        <span className="inline-flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-current shrink-0" />
          <span>{typeof children === "string" ? "Loading..." : children}</span>
        </span>
      ) : (
        <>
          {LeftIcon && <LeftIcon className="h-4 w-4 shrink-0 transition-transform group-hover:-translate-x-0.5" />}
          <span>{children}</span>
          {RightIcon && <RightIcon className="h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5" />}
        </>
      )}
    </motion.button>
  );
}
