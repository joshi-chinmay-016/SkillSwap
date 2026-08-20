import React from "react";

export default function ShinyText({
  text,
  disabled = false,
  speed = 4.5,
  className = "",
}) {
  return (
    <span
      className={`relative inline-block font-heading tracking-tight bg-[linear-gradient(110deg,#4f46e5,35%,#a855f7,50%,#ec4899,65%,#4f46e5)] dark:bg-[linear-gradient(110deg,#a5b4fc,35%,#ffffff,50%,#c084fc,65%,#a5b4fc)] bg-[length:250%_100%] bg-clip-text text-transparent ${
        !disabled ? "animate-shine" : ""
      } ${className}`}
      style={{
        animationDuration: `${speed}s`,
      }}
    >
      {text}
    </span>
  );
}
