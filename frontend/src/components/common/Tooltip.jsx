import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";

export default function Tooltip({
  content,
  children,
  position = "top",
  delay = 200,
  className = "",
  ...props
}) {
  const [isVisible, setIsVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const timeoutRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
    } else {
      timeoutRef.current = setTimeout(() => {
        setShouldRender(false);
      }, 150);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isVisible]);

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  const positionStyles = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  const arrowStyles = {
    top: "top-full left-1/2 -translate-x-1/2 border-t-border-l bg-bg-alt",
    bottom: "bottom-full left-1/2 -translate-x-1/2 border-b-border-l bg-bg-alt",
    left: "left-full top-1/2 -translate-y-1/2 border-l-border-l bg-bg-alt",
    right: "right-full top-1/2 -translate-y-1/2 border-r-border-l bg-bg-alt",
  };

  return (
    <div
      ref={containerRef}
      className="relative inline-flex"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
      {...props}
    >
      {children}

      <AnimatePresence>
        {shouldRender && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: isVisible ? 1 : 0, scale: isVisible ? 1 : 0.9 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.1 }}
            className={`
              absolute z-50 px-2.5 py-1.5 bg-bg-alt border border-border rounded-md
              text-xs text-text shadow-md max-w-xs whitespace-nowrap
              ${positionStyles[position]}
              ${className}
            `}
            role="tooltip"
          >
            {content}
            {/* Arrow */}
            <div
              className={`
                absolute w-1.5 h-1.5 bg-bg-alt border border-border
                ${position === "top" && "border-t-0 border-l-0 rotate-45 -bottom-[5px]"}
                ${position === "bottom" && "border-b-0 border-r-0 rotate-45 -top-[5px]"}
                ${position === "left" && "border-t-0 border-t-0 rotate-45 -right-[5px]"}
                ${position === "right" && "border-b-0 border-l-0 rotate-45 -left-[5px]"}
              `}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}