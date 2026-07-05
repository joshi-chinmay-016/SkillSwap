import React, { useState, useCallback, createContext, useContext } from "react";
import { motion, AnimatePresence } from "motion/react";
import { CheckCircle, AlertCircle, Info, X } from "lucide-react";

const ToastContext = createContext(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertCircle,
  info: Info,
};

const variants = {
  success: "bg-green-500/10 border-green-500/20 text-green-600",
  error: "bg-danger/10 border-danger/20 text-danger",
  warning: "bg-yellow-500/10 border-yellow-500/20 text-yellow-600",
  info: "bg-accent/10 border-accent/20 text-accent",
};

function ToastItem({ toast, onDismiss }) {
  const Icon = icons[toast.type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.9 }}
      transition={{ duration: 0.2 }}
      className={`
        flex items-center gap-3 px-4 py-3 rounded-lg border shadow-md
        bg-bg border-border max-w-sm w-full
      `}
    >
      <Icon size={18} className={`shrink-0 ${variants[toast.type].split(" ").pop()}`} />
      <div className="flex-1 min-w-0">
        {toast.title && (
          <p className="text-xs font-semibold text-text">{toast.title}</p>
        )}
        <p className="text-xs text-text-secondary mt-0.5">{toast.message}</p>
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 p-1 rounded hover:bg-bg-alt text-text-secondary hover:text-text transition-colors cursor-pointer"
        aria-label="Dismiss"
      >
        <X size={14} />
      </button>
    </motion.div>
  );
}

function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="fixed top-20 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={removeToast} />
        ))}
      </AnimatePresence>
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id = Date.now();
    const newToast = {
      id,
      type: toast.type || "info",
      title: toast.title,
      message: toast.message,
      duration: toast.duration || 4000,
    };

    setToasts((prev) => [...prev, newToast]);

    if (newToast.duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, newToast.duration);
    }

    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const success = useCallback((message, title) => {
    return addToast({ type: "success", message, title });
  }, [addToast]);

  const error = useCallback((message, title) => {
    return addToast({ type: "error", message, title });
  }, [addToast]);

  const warning = useCallback((message, title) => {
    return addToast({ type: "warning", message, title });
  }, [addToast]);

  const info = useCallback((message, title) => {
    return addToast({ type: "info", message, title });
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ addToast, removeToast, success, error, warning, info }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

export default ToastProvider;