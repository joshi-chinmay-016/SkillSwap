import React from "react";
import { motion } from "motion/react";
import { AlertCircle, RefreshCw } from "lucide-react";
import Button from "./Button";

export default function ErrorState({
  title = "Something went wrong",
  message = "We encountered an error while fetching your data. Please try again.",
  onRetry,
  className = "",
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`rounded-2xl border border-danger/20 bg-danger/5 p-8 text-center flex flex-col items-center justify-center max-w-lg mx-auto ${className}`}
    >
      <div className="w-12 h-12 rounded-xl bg-danger/10 text-danger flex items-center justify-center mb-3">
        <AlertCircle size={24} />
      </div>
      <h3 className="text-base font-semibold text-text mb-1">{title}</h3>
      <p className="text-xs sm:text-sm text-text-secondary mb-5 max-w-sm">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} leftIcon={RefreshCw}>
          Try Again
        </Button>
      )}
    </motion.div>
  );
}
