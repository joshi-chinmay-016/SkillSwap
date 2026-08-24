import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  TrendingUp,
  Award,
  Calendar,
  Users,
  CheckCircle2,
  PieChart as PieIcon
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  PieChart,
  Pie
} from "recharts";
import { getAdminAnalytics } from "../../api/adminApi";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

export default function AdminAnalytics() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin", "analytics"],
    queryFn: getAdminAnalytics,
  });

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-24 bg-slate-800/40 rounded-2xl border border-slate-800" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 bg-slate-800/40 rounded-2xl border border-slate-800" />
          <div className="h-80 bg-slate-800/40 rounded-2xl border border-slate-800" />
        </div>
      </div>
    );
  }

  const topSkills = data?.top_skills || [];
  const sessionBreakdown = data?.session_breakdown || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Platform Analytics & Insights</h1>
        <p className="text-sm text-slate-400">
          Derived from live database aggregations. Skill popularity, session completion rates, and learning distribution.
        </p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Users</span>
          <div className="text-3xl font-bold text-white">{data?.total_users || 0}</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Sessions</span>
          <div className="text-3xl font-bold text-indigo-400">{data?.total_sessions || 0}</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Completed Sessions</span>
          <div className="text-3xl font-bold text-emerald-400">{data?.completed_sessions || 0}</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Completion Rate</span>
          <div className="text-3xl font-bold text-slate-200">{data?.completion_rate || 0}%</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Skills Chart */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-slate-200">Top Verified Teaching Skills</h2>
          </div>

          <div className="h-72 w-full pt-4">
            {topSkills.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topSkills} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <XAxis type="number" stroke="#64748b" fontSize={11} />
                  <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={12} width={100} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.75rem" }}
                    labelStyle={{ color: "#f8fafc", fontWeight: 600 }}
                  />
                  <Bar dataKey="mentors" fill="#6366f1" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                Insufficient skill verification data available.
              </div>
            )}
          </div>
        </div>

        {/* Session Status Distribution */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-slate-200">Session Status Distribution</h2>
          </div>

          <div className="h-72 w-full pt-4">
            {sessionBreakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sessionBreakdown}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    innerRadius={50}
                    paddingAngle={4}
                    label={({ status, count }) => `${status}: ${count}`}
                  >
                    {sessionBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.75rem" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No session distribution history recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
