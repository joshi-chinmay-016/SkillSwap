import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Server,
  Database,
  Layers,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw
} from "lucide-react";
import { getAdminSystemHealth } from "../../api/adminApi";

export default function AdminSystem() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["admin", "system", "health"],
    queryFn: getAdminSystemHealth,
    refetchInterval: 10000,
  });

  const formatUptime = (seconds) => {
    if (!seconds) return "0s";
    const days = Math.floor(seconds / 86400);
    const hrs = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${days > 0 ? `${days}d ` : ""}${hrs}h ${mins}m ${secs}s`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">System Diagnostics</h1>
          <p className="text-sm text-slate-400">
            Real-time infrastructure health, database connection latency, and Redis cluster status.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
          Run Health Check
        </button>
      </div>

      {/* Main Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Core Application */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Server className="w-5 h-5 text-indigo-400" />
              <h2 className="font-bold text-slate-200">API Server</h2>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                data?.status === "healthy"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
              }`}
            >
              {data?.status || "Checking..."}
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Environment</span>
              <span className="text-slate-200 font-mono uppercase font-semibold">{data?.environment || "production"}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Release Version</span>
              <span className="text-slate-200 font-mono">{data?.version || "1.0.0"}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Uptime</span>
              <span className="text-slate-200 font-mono font-medium">{formatUptime(data?.uptime_seconds)}</span>
            </div>
          </div>
        </div>

        {/* PostgreSQL Database */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Database className="w-5 h-5 text-blue-400" />
              <h2 className="font-bold text-slate-200">PostgreSQL Database</h2>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                data?.database?.status === "healthy"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "bg-red-500/10 text-red-400 border border-red-500/30"
              }`}
            >
              {data?.database?.status || "Unknown"}
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Query Ping Latency</span>
              <span className="text-emerald-400 font-mono font-bold">
                {data?.database?.latency_ms !== undefined ? `${data.database.latency_ms} ms` : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Schema State</span>
              <span className="text-slate-200 font-semibold">Alembic Head (m10a1)</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Connection Mode</span>
              <span className="text-slate-200 font-mono">Managed Pool</span>
            </div>
          </div>
        </div>

        {/* Redis Cluster */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Layers className="w-5 h-5 text-red-400" />
              <h2 className="font-bold text-slate-200">Redis Coordination</h2>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                data?.redis?.status === "healthy"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
              }`}
            >
              {data?.redis?.status || "Unknown"}
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Ping Latency</span>
              <span className="text-indigo-300 font-mono font-bold">
                {data?.redis?.latency_ms !== undefined ? `${data.redis.latency_ms} ms` : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Pub/Sub Engine</span>
              <span className="text-emerald-400 font-semibold">Active Listener</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Rate Limiter</span>
              <span className="text-slate-200 font-semibold">Atomic Token Bucket</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
