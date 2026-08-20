import React, { useState } from "react";

export default function InfiniteMarquee({
  items = [],
  reverse = false,
  speed = 28,
  className = "",
}) {
  const [isPaused, setIsPaused] = useState(false);
  const rawId = React.useId();
  const safeId = "mq_" + rawId.replace(/[^a-zA-Z0-9]/g, "");

  // Repeat items 4 times to ensure seamless infinite looping across all viewport widths
  const repetitions = [0, 1, 2, 3];

  return (
    <div
      className={`group relative w-full overflow-hidden select-none py-1.5 ${className}`}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <style>{`
        @keyframes ${safeId}-forward {
          0% { transform: translate3d(0, 0, 0); }
          100% { transform: translate3d(-50%, 0, 0); }
        }
        @keyframes ${safeId}-reverse {
          0% { transform: translate3d(-50%, 0, 0); }
          100% { transform: translate3d(0, 0, 0); }
        }
        .${safeId}-track {
          display: flex;
          width: max-content;
          will-change: transform;
          animation-name: ${reverse ? `${safeId}-reverse` : `${safeId}-forward`};
          animation-duration: ${speed}s;
          animation-timing-function: linear;
          animation-iteration-count: infinite;
          animation-play-state: ${isPaused ? "paused" : "running"};
        }
        .${safeId}-track:hover {
          animation-play-state: paused !important;
        }
      `}</style>

      {/* Edge gradient fade masks */}
      <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-16 sm:w-32 bg-gradient-to-r from-bg to-transparent z-10" />
      <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-16 sm:w-32 bg-gradient-to-l from-bg to-transparent z-10" />

      <div className={`${safeId}-track`}>
        {repetitions.map((repIndex) => (
          <div
            key={`rep-${repIndex}`}
            className="flex items-center gap-3 sm:gap-4 shrink-0 pr-3 sm:pr-4"
          >
            {items.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={`item-${repIndex}-${idx}`}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-surface-elevated border border-border text-xs sm:text-sm font-bold text-text shadow-sm hover:border-accent/60 hover:scale-105 transition-all duration-200 cursor-pointer"
                >
                  {Icon && (
                    <Icon size={16} className={item.color || "text-accent"} />
                  )}
                  <span>{item.name}</span>
                  {item.badge && (
                    <span className="text-[10px] uppercase font-black px-2 py-0.5 rounded-md bg-accent/15 text-accent border border-accent/25">
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
