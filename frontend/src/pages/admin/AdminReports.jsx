import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  X,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { getAdminReports, resolveAdminReport } from "../../api/adminApi";
import { useToast } from "../../components/common/Toast";

export default function AdminReports() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const [selectedReport, setSelectedReport] = useState(null);
  const [targetStatus, setTargetStatus] = useState("RESOLVED");
  const [resolutionNotes, setResolutionNotes] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "reports", statusFilter, page],
    queryFn: () =>
      getAdminReports({
        status: statusFilter || undefined,
        page,
        size: 15,
      }),
  });

  const resolveMutation = useMutation({
    mutationFn: ({ reportId, status, resolutionNotes }) =>
      resolveAdminReport(reportId, status, resolutionNotes),
    onSuccess: (res) => {
      addToast(res.message || "Report resolved", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "reports"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to update report", "error");
    },
  });

  const closeModal = () => {
    setSelectedReport(null);
    setResolutionNotes("");
  };

  const handleResolve = (e) => {
    e.preventDefault();
    if (!resolutionNotes.trim()) {
      addToast("Resolution notes are mandatory for the audit log.", "warning");
      return;
    }
    resolveMutation.mutate({
      reportId: selectedReport.id,
      status: targetStatus,
      resolutionNotes,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Platform Moderation & Reports</h1>
        <p className="text-sm text-slate-400">
          Investigate user conduct flags, review filed complaints, and record resolution outcomes with audit safety.
        </p>
      </div>

      {/* Filter */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Moderation Statuses</option>
          <option value="OPEN">Open</option>
          <option value="UNDER_REVIEW">Under Review</option>
          <option value="RESOLVED">Resolved</option>
          <option value="DISMISSED">Dismissed</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3.5 px-4">Report ID</th>
                <th className="py-3.5 px-4">Reporter</th>
                <th className="py-3.5 px-4">Reported Account</th>
                <th className="py-3.5 px-4">Reason / Complaint</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Filed At</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    Loading moderation queue...
                  </td>
                </tr>
              ) : data?.items?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    No moderation reports found.
                  </td>
                </tr>
              ) : (
                data?.items?.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      #{r.id}
                    </td>

                    <td className="py-3.5 px-4 text-xs">
                      <div className="font-semibold text-slate-200">{r.reporter.name}</div>
                      <div className="text-slate-500 font-mono">{r.reporter.email}</div>
                    </td>

                    <td className="py-3.5 px-4 text-xs">
                      {r.reported_user ? (
                        <>
                          <div className="font-semibold text-slate-200">{r.reported_user.name}</div>
                          <div className="text-slate-500 font-mono">{r.reported_user.email}</div>
                        </>
                      ) : (
                        <span className="text-slate-500">Platform report</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-300 max-w-xs">
                      <p className="line-clamp-2">{r.reason}</p>
                      {r.resolution_notes && (
                        <p className="text-indigo-400 text-[11px] mt-1 line-clamp-1">
                          Resolution: {r.resolution_notes}
                        </p>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${
                          r.status === "RESOLVED"
                            ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
                            : r.status === "OPEN"
                            ? "bg-red-500/10 border border-red-500/30 text-red-400"
                            : r.status === "UNDER_REVIEW"
                            ? "bg-amber-500/10 border border-amber-500/30 text-amber-300"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => {
                          setSelectedReport(r);
                          setTargetStatus(r.status === "OPEN" ? "RESOLVED" : r.status);
                          setResolutionNotes(r.resolution_notes || "");
                        }}
                        className="px-2.5 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition-colors"
                      >
                        Resolve
                      </button>
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
            <strong className="text-slate-200">{data?.total_pages || 1}</strong> ({data?.total || 0} reports)
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

      {/* Resolution Dialog */}
      {selectedReport && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="max-w-md w-full rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100">Resolve Report #{selectedReport.id}</h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleResolve} className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-slate-400">Reporter: <strong className="text-slate-200">{selectedReport.reporter.name}</strong></div>
                <div className="text-slate-400">Reported: <strong className="text-slate-200">{selectedReport.reported_user?.name || "Platform"}</strong></div>
                <div className="text-slate-400 pt-1">Reason: <span className="text-slate-300 italic">{selectedReport.reason}</span></div>
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Update Status</label>
                <select
                  value={targetStatus}
                  onChange={(e) => setTargetStatus(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                  <option value="RESOLVED">RESOLVED</option>
                  <option value="DISMISSED">DISMISSED</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Resolution Notes</label>
                <textarea
                  rows="3"
                  required
                  placeholder="Document actions taken or findings..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/20"
                >
                  Submit Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
