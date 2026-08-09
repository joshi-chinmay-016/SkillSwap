import React, { useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Database, Sparkles, Shield, Cpu } from "lucide-react";

/**
 * Conceptual 3D Vector Space Canvas Visualization.
 * Renders an abstract vector constellation/mesh representing indexed float32 vectors.
 * Supports prefers-reduced-motion and dark/light modes.
 * IMPORTANT: Strictly conceptual — raw vector values are never exposed or transmitted.
 */
export default function VectorIndexVisualization({
  vectorCount = 0,
  dimension = 768,
  indexType = "FAISS CPU (IndexFlatIP)",
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let animationFrameId;

    // Set high DPI canvas resolution
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Node count proportional to vectorCount (clamped 20-50 nodes for performance)
    const nodeCount = Math.min(50, Math.max(20, Math.floor(vectorCount / 10) || 25));

    // Generate random nodes in 3D-projected space
    const nodes = Array.from({ length: nodeCount }, () => ({
      x: Math.random() * rect.width,
      y: Math.random() * rect.height,
      z: Math.random() * 200 + 50,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      radius: Math.random() * 2.5 + 1.5,
    }));

    const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function render() {
      ctx.clearRect(0, 0, rect.width, rect.height);

      // Draw connecting lines (vector inner-product edges)
      ctx.strokeStyle = "rgba(99, 102, 241, 0.15)";
      ctx.lineWidth = 1;

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 100) {
            const alpha = (1 - dist / 100) * 0.25;
            ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw vector nodes
      nodes.forEach((node) => {
        if (!isReducedMotion) {
          node.x += node.vx;
          node.y += node.vy;

          if (node.x < 0 || node.x > rect.width) node.vx *= -1;
          if (node.y < 0 || node.y > rect.height) node.vy *= -1;
        }

        const scale = 150 / node.z;
        const opacity = Math.min(1, Math.max(0.2, scale));

        ctx.fillStyle = `rgba(20, 184, 166, ${opacity})`;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius * scale, 0, Math.PI * 2);
        ctx.fill();

        // Glow ring
        ctx.strokeStyle = `rgba(99, 102, 241, ${opacity * 0.5})`;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius * scale * 2, 0, Math.PI * 2);
        ctx.stroke();
      });

      if (!isReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    }

    render();

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, [vectorCount]);

  return (
    <div className="relative w-full h-44 rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 border border-slate-800 overflow-hidden p-4 flex flex-col justify-between shadow-inner">
      {/* 3D Canvas Mesh Overlay */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />

      {/* Header Info */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-teal-500/20 text-teal-300 border border-teal-500/30">
            <Database size={14} />
          </span>
          <span className="text-xs font-black text-white tracking-wide uppercase">
            FAISS Vector Index Space
          </span>
        </div>

        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-800/80 text-teal-300 border border-slate-700">
          {dimension}-D Float32 Space
        </span>
      </div>

      {/* Center Stats Badge */}
      <div className="relative z-10 flex items-center justify-center">
        <div className="px-4 py-2 rounded-xl bg-slate-900/80 backdrop-blur-md border border-indigo-500/30 text-center shadow-lg">
          <div className="text-lg font-black text-white tracking-tight">
            {vectorCount.toLocaleString()} <span className="text-xs font-semibold text-teal-400">Indexed Vectors</span>
          </div>
          <p className="text-[10px] text-slate-400 font-medium mt-0.5">
            {indexType}
          </p>
        </div>
      </div>

      {/* Footer Security Note */}
      <div className="relative z-10 flex items-center justify-between text-[10px] text-slate-400 font-semibold border-t border-slate-800/80 pt-2">
        <span className="flex items-center gap-1">
          <Shield size={11} className="text-emerald-400" />
          Server-Side FAISS CPU Storage
        </span>
        <span className="flex items-center gap-1">
          <Cpu size={11} className="text-indigo-400" />
          Exact Inner-Product Cosine Similarity
        </span>
      </div>
    </div>
  );
}
