import React, { useRef, useState } from "react";
import { motion } from "motion/react";

export default function Card3DTilt({
  children,
  className = "",
  maxTilt = 12,
  glare = true,
  onClick,
}) {
  const cardRef = useRef(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [glarePos, setGlarePos] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rX = ((y - centerY) / centerY) * -maxTilt;
    const rY = ((x - centerX) / centerX) * maxTilt;

    setRotateX(rX);
    setRotateY(rY);

    if (glare) {
      setGlarePos({
        x: (x / rect.width) * 100,
        y: (y / rect.height) * 100,
        opacity: 0.18,
      });
    }
  };

  const handleMouseLeave = () => {
    setRotateX(0);
    setRotateY(0);
    if (glare) {
      setGlarePos((prev) => ({ ...prev, opacity: 0 }));
    }
  };

  return (
    <div
      style={{ perspective: 1000 }}
      className={`w-full ${onClick ? "cursor-pointer" : ""}`}
      onClick={onClick}
    >
      <motion.div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        animate={{
          rotateX,
          rotateY,
        }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        style={{
          transformStyle: "preserve-3d",
        }}
        className={`relative rounded-3xl border border-card-border bg-card-bg overflow-hidden transition-shadow duration-300 hover:shadow-2xl hover:border-accent/40 ${className}`}
      >
        {glare && (
          <div
            className="pointer-events-none absolute -inset-px transition-opacity duration-300 z-30"
            style={{
              opacity: glarePos.opacity,
              background: `radial-gradient(350px circle at ${glarePos.x}% ${glarePos.y}%, rgba(255, 255, 255, 0.25), transparent 80%)`,
            }}
          />
        )}
        <div style={{ transform: "translateZ(20px)" }} className="relative z-10">
          {children}
        </div>
      </motion.div>
    </div>
  );
}
