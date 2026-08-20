import React from "react";
import { motion } from "motion/react";

export function PushPin({ color = "red", className = "" }) {
  const pinColors = {
    red: "bg-rose-500 shadow-rose-500/50",
    yellow: "bg-amber-400 shadow-amber-400/50",
    cyan: "bg-sky-400 shadow-sky-400/50",
    purple: "bg-purple-500 shadow-purple-500/50",
    green: "bg-emerald-500 shadow-emerald-500/50",
  };

  const selectedColor = pinColors[color] || pinColors.red;

  return (
    <div className={`absolute -top-3.5 left-1/2 -translate-x-1/2 z-30 flex flex-col items-center pointer-events-none ${className}`}>
      {/* 3D Pin Head */}
      <div className={`w-5 h-5 rounded-full ${selectedColor} shadow-md border-2 border-white/80 ring-1 ring-black/10 relative flex items-center justify-center`}>
        {/* Specular Highlight */}
        <div className="w-1.5 h-1.5 rounded-full bg-white/90 absolute top-0.5 left-1" />
      </div>
      {/* Pin Shadow */}
      <div className="w-2 h-1 bg-black/20 rounded-full blur-[1px] -mt-0.5" />
    </div>
  );
}

export default function PinnedCard({
  children,
  pinColor = "red",
  sway = "left", // 'left', 'right', or 'none'
  tape = false,
  note = "",
  className = "",
  onClick,
}) {
  const swayClass =
    sway === "left"
      ? "animate-sway-left"
      : sway === "right"
      ? "animate-sway-right"
      : "";

  return (
    <div
      onClick={onClick}
      style={{ perspective: 1000 }}
      className={`relative group ${onClick ? "cursor-pointer" : ""} ${swayClass}`}
    >
      {/* Pushpin */}
      {!tape && <PushPin color={pinColor} />}

      {/* Washi Tape Strip Option */}
      {tape && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-30 w-16 h-6 bg-amber-200/85 dark:bg-amber-400/50 border border-amber-300/60 rotate-[-2deg] backdrop-blur-xs shadow-xs" />
      )}

      {/* Hand-drawn sticky note callout */}
      {note && (
        <div className="absolute -top-4 -right-3 z-30 font-handwriting text-base sm:text-lg font-bold text-rose-600 dark:text-rose-400 rotate-6 px-2 py-0.5 bg-yellow-100 dark:bg-yellow-950 border border-yellow-300 dark:border-yellow-800 rounded-lg shadow-sm">
          {note}
        </div>
      )}

      {/* Main Pinned Surface Card */}
      <div
        className={`relative rounded-2xl border border-card-border bg-card-bg/95 backdrop-blur-md shadow-md group-hover:shadow-xl group-hover:border-accent/50 group-hover:scale-[1.02] transition-all duration-300 p-5 ${className}`}
      >
        {children}
      </div>
    </div>
  );
}
