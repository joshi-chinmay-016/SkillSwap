import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Calendar,
  Search,
  XCircle,
  ExternalLink,
  Clock,
  User,
  ChevronLeft,
  ChevronRight,
  X,
  RefreshCw
} from "lucide-react";
import { getAdminSessions, cancelAdminSession } from "../../api/adminApi";
import { useToast } from "../../components/common/Toast";

export default function AdminSessions() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const [selectedSession, setSelectedSession] = useState(null);
  const [cancelReason, setCancelReason] = useState("");
  const [refundCoins, setRefundCoins] = useState(true);

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "sessions", search, statusFilter, page],
    queryFn: () =>
      getAdminSessions({
        search: search || undefined,
        status: statusFilter || undefined,
        page,
        size: 15,
      }),
  });

  const cancelMutation = useMutation({
    mutationFn: ({ sessionId, reason, refundCoins }) =>
      cancelAdminSession(sessionId, reason, refundCoins),
    onSuccess: (res) => {
      addToast(
        res.refund_issued
          ? "Session cancelled administratively and learner coin was refunded."
          : "Session cancelled administratively.",
        "success"
      );
      queryClient.invalidateQueries({ queryKey: ["admin", "sessions"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to cancel session", "error");
    },
  });

  const closeModal = () => {
    setSelectedSession(null);
    setCancelReason("");
    setRefundCoins(true);
  };

  const handleCancelSubmit = (e) => {
    e.preventDefault();
    if (!cancelReason.trim()) {
      addToast("A mandatory cancellation explanation is required for the audit log.", "warning");
      return;
    }
    cancelMutation.mutate({
      sessionId: selectedSession.id,
      reason: cancelReason,
      refundCoins,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Session Oversight</h1>
        <p className="text-sm text-slate-400">
          Monitor scheduled, active, and completed peer mentoring sessions, and handle administrative cancellations with automated refunds.
        </p>
      </div>

      {/* Filters */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by skill name..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Session Statuses</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3.5 px-4">Session ID</th>
                <th className="py-3.5 px-4">Skill</th>
                <th className="py-3.5 px-4">Mentor</th>
                <th className="py-3.5 px-4">Learner</th>
                <th className="py-3.5 px-4">Scheduled Time</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    Loading session records...
                  </td>
                </tr>
              ) : data?.items?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    No sessions found.
                  </td>
                </tr>
              ) : (
                data?.items?.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      #{s.id}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="font-semibold text-slate-200">{s.skill.name}</span>
                    </td>

                    <td className="py-3.5 px-4 text-xs">
                      <div className="font-medium text-slate-200">{s.mentor.name}</div>
                      <div className="text-slate-500 font-mono">{s.mentor.email}</div>
                    </td>

                    <td className="py-3.5 px-4 text-xs">
                      <div className="font-medium text-slate-200">{s.learner.name}</div>
                      <div className="text-slate-500 font-mono">{s.learner.email}</div>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-300">
                      {s.scheduled_at ? new Date(s.scheduled_at).toLocaleString() : "—"}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${
                          s.status === "completed"
                            ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
                            : s.status === "scheduled"
                            ? "bg-indigo-500/10 border border-indigo-500/30 text-indigo-300"
                            : s.status === "in_progress"
                            ? "bg-amber-500/10 border border-amber-500/30 text-amber-300 animate-pulse"
                            : "bg-red-500/10 border border-red-500/30 text-red-400"
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      {s.status === "scheduled" || s.status === "in_progress" ? (
                        <button
                          onClick={() => setSelectedSession(s)}
                          className="px-2.5 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-semibold transition-colors"
                        >
                          Cancel
                        </button>
                      ) : (
                        <span className="text-xs text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <strong className="text-slate-200">{data?.page || 1}</strong> of{" "}
            <strong className="text-slate-200">{data?.total_pages || 1}</strong> ({data?.total || 0} sessions)
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-40 hover:bg-slate-800 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= (data?.total_pages || 1)}
              onClick={() => setPage((p) => p + 1)}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-40 hover:bg-slate-800 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Cancellation Modal */}
      {selectedSession && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="max-w-md w-full rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100">Cancel Session #{selectedSession.id}</h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCancelSubmit} className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-slate-400">Topic: <strong className="text-slate-200">{selectedSession.skill.name}</strong></div>
                <div className="text-slate-400">Mentor: <strong className="text-slate-200">{selectedSession.mentor.name}</strong></div>
                <div className="text-slate-400">Learner: <strong className="text-slate-200">{selectedSession.learner.name}</strong></div>
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Mandatory Cancellation Reason</label>
                <textarea
                  rows="3"
                  required
                  placeholder="Explain why this session is being cancelled administratively..."
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <label className="flex items-center gap-2.5 cursor-pointer p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <input
                  type="checkbox"
                  checked={refundCoins}
                  onChange={(e) => setRefundCoins(e.target.checked)}
                  className="rounded border-slate-700 text-indigo-600 focus:ring-0"
                />
                <span className="text-slate-300">Refund 1 coin back to learner wallet</span>
              </label>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white font-semibold shadow-lg shadow-red-600/20"
                >
                  Confirm Cancellation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
