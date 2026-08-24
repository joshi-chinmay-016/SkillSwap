import React, { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Award,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Coins,
  Server,
  Activity,
  ArrowUpRight,
  ShieldCheck,
  Clock,
  Sparkles
} from "lucide-react";
import { getAdminDashboard, getAdminAuditLogs } from "../../api/adminApi";
import * as THREE from "three";

export default function AdminDashboard() {
  const canvasRef = useRef(null);

  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: getAdminDashboard,
    refetchInterval: 15000,
  });

  const { data: auditData } = useQuery({
    queryKey: ["admin", "audit-logs", "recent"],
    queryFn: () => getAdminAuditLogs({ size: 5 }),
    refetchInterval: 15000,
  });

  // Three.js subtle ambient background particle network
  useEffect(() => {
    if (!canvasRef.current) return;
    const container = canvasRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.z = 80;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const particleCount = 60;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 120;
      positions[i + 1] = (Math.random() - 0.5) * 60;
      positions[i + 2] = (Math.random() - 0.5) * 40;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: 0x6366f1,
      size: 1.8,
      transparent: true,
      opacity: 0.35,
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      particles.rotation.y += 0.0006;
      particles.rotation.x += 0.0003;
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 bg-slate-800/40 rounded-2xl border border-slate-800" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-32 bg-slate-800/40 rounded-2xl border border-slate-800" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 rounded-2xl bg-red-500/10 border border-red-500/30 text-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
        <h3 className="text-lg font-bold text-red-200">Failed to load platform metrics</h3>
        <p className="text-sm text-slate-400">{error.message || "An unexpected error occurred."}</p>
      </div>
    );
  }

  const u = metrics?.users || { total: 0, active: 0, suspended: 0 };
  const s = metrics?.sessions || { total: 0, completed: 0, upcoming: 0, cancelled: 0, completion_rate: 0 };
  const m = metrics?.mentors || { verified_count: 0, pending_verifications: 0 };
  const w = metrics?.wallet || { total_circulation: 0, total_transactions: 0 };
  const mod = metrics?.moderation || { open_reports: 0 };
  const sys = metrics?.system || { status: "healthy", redis: "healthy", uptime_seconds: 0 };

  const formatUptime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hrs}h ${mins}m`;
  };

  return (
    <div className="space-y-8 relative">
      {/* Three.js Canvas Header Backdrop */}
      <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 p-6 sm:p-8 shadow-2xl">
        <div ref={canvasRef} className="absolute inset-0 pointer-events-none opacity-60" />
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-xs font-semibold text-indigo-300">
            <Sparkles className="w-3.5 h-3.5" />
            SkillSwap Arena Platform Console
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Platform Command Center
          </h1>
          <p className="text-slate-400 text-sm max-w-2xl">
            Live authoritative platform metrics, user access controls, mentor verifications, and append-only audit trail.
          </p>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Total Users */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-md space-y-3 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Users</span>
            <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white tracking-tight">{u.total}</div>
            <div className="text-xs text-slate-400">
              <span className="text-emerald-400 font-semibold">{u.active}</span> active
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Suspended: <strong className="text-slate-300">{u.suspended}</strong></span>
            <Link to="/admin/users" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              Manage <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Verified Mentors & Queue */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-md space-y-3 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Verified Mentors</span>
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white tracking-tight">{m.verified_count}</div>
            {m.pending_verifications > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
                {m.pending_verifications} pending
              </span>
            )}
          </div>
          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Pending review: <strong className="text-amber-400">{m.pending_verifications}</strong></span>
            <Link to="/admin/verification" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              Review <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Sessions & Completion */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-md space-y-3 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Sessions</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white tracking-tight">{s.total}</div>
            <div className="text-xs text-slate-400">
              <span className="text-emerald-400 font-semibold">{s.completion_rate}%</span> completed
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Upcoming: <strong className="text-indigo-300">{s.upcoming}</strong></span>
            <Link to="/admin/sessions" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              Inspect <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Economy & Wallet */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-md space-y-3 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Coin Economy</span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Coins className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white tracking-tight">{w.total_circulation} <span className="text-xs text-amber-400">🪙</span></div>
            <div className="text-xs text-slate-400">{w.total_transactions} txs</div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Open reports: <strong className={mod.open_reports > 0 ? "text-red-400" : "text-slate-300"}>{mod.open_reports}</strong></span>
            <Link to="/admin/wallet" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              Oversight <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* System Status & Quick Action Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-slate-200">System Infrastructure</h2>
            </div>
            <Link to="/admin/system" className="text-xs text-indigo-400 hover:underline">
              Diagnostics
            </Link>
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
              <span className="text-slate-400">Platform Status</span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold uppercase">
                {sys.status}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
              <span className="text-slate-400">Redis Coordination</span>
              <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 font-semibold uppercase">
                {sys.redis}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
              <span className="text-slate-400">Backend Uptime</span>
              <span className="text-slate-200 font-mono font-medium">
                {formatUptime(sys.uptime_seconds)}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Action Matrix */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-slate-200">Operational Queues</h2>
          </div>

          <div className="space-y-2 pt-2">
            <Link
              to="/admin/verification"
              className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800 transition-colors text-xs"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-400" />
                <span className="text-slate-300 font-medium">Mentor Verifications</span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-bold">
                {m.pending_verifications}
              </span>
            </Link>

            <Link
              to="/admin/reports"
              className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800 transition-colors text-xs"
            >
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <span className="text-slate-300 font-medium">Moderation Reports</span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 font-bold">
                {mod.open_reports}
              </span>
            </Link>

            <Link
              to="/admin/skills"
              className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800 transition-colors text-xs"
            >
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-indigo-400" />
                <span className="text-slate-300 font-medium">Manage Platform Skills</span>
              </div>
              <span className="text-slate-500">Configure</span>
            </Link>
          </div>
        </div>

        {/* Recent Audit Activity */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-slate-200">Recent Audit Logs</h2>
            </div>
            <Link to="/admin/audit-logs" className="text-xs text-indigo-400 hover:underline">
              View All
            </Link>
          </div>

          <div className="space-y-2 pt-1">
            {auditData?.items && auditData.items.length > 0 ? (
              auditData.items.map((log) => (
                <div key={log.id} className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/60 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-indigo-300 font-mono">{log.action}</span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">
                    {log.reason || `Target: ${log.target_type} #${log.target_id}`}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">
                No recent administrative actions recorded.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
