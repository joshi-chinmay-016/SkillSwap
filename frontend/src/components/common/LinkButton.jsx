import React from "react";
import { Link } from "react-router-dom";

export default function LinkButton({
  children,
  to,
  variant = "primary",
  size = "md",
  disabled = false,
  className = "",
  ...props
}) {
  const baseClasses = "inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50 disabled:cursor-not-allowed";

  const variantClasses = {
    primary: "bg-accent text-white hover:bg-accent-hover active:bg-accent-hover/90",
    secondary: "bg-bg-alt text-text border border-border hover:bg-border active:bg-border/80",
    outline: "bg-transparent text-accent border border-accent hover:bg-accent/10 active:bg-accent/20",
    ghost: "bg-transparent text-text hover:bg-bg-alt active:bg-border/50",
    danger: "bg-danger text-white hover:bg-danger/90 active:bg-danger/80",
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-2.5 text-base",
  };

  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;

  if (disabled) {
    return (
      <span className={classes} {...props}>
        {children}
      </span>
    );
  }

  return (
    <Link to={to} className={classes} {...props}>
      {children}
    </Link>
  );
}
