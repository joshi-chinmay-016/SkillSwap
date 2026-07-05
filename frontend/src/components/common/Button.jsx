import React from "react";
import { motion } from "motion/react";

export default function Button({
  children,
  onClick,
  type = "button",
  variant = "primary",
  size = "md",
  disabled = false,
  isLoading = false,
  className = "",
  ...props
}) {
  const baseStyles = "inline-flex items-center justify-center font-medium rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-50 disabled:pointer-events-none cursor-pointer";
  
  const variants = {
    primary: "bg-accent text-white hover:bg-accent-hover shadow-sm",
    secondary: "bg-bg-alt text-text border border-border hover:bg-border hover:text-text",
    outline: "bg-transparent text-text border border-border hover:bg-bg-alt",
    danger: "bg-danger text-white hover:bg-red-600 shadow-sm focus-visible:outline-danger",
    ghost: "bg-transparent text-text hover:bg-bg-alt",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-6 py-3 text-base gap-2.5",
  };

  const currentStyles = `${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`;

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled || isLoading}
      whileHover={disabled || isLoading ? {} : { scale: 1.015 }}
      whileTap={disabled || isLoading ? {} : { scale: 0.985 }}
      transition={{ duration: 0.1, ease: "easeInOut" }}
      className={currentStyles}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </motion.button>
  );
}
