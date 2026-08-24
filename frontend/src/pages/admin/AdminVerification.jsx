import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  XCircle,
  Search,
  Check,
  X,
  Clock,
  Award,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { getAdminVerifications, approveAdminVerification, rejectAdminVerification } from "../../api/adminApi";
import { useToast } from "../../components/common/Toast";

export default function AdminVerification() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const [selectedRecord, setSelectedRecord] = useState(null);
  const [modalMode, setModalMode] = useState(null); // 'approve' | 'reject'
  const [reason, setReason] = useState("");
  const [scoreOverride, setScoreOverride] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "verification", search, statusFilter, page],
    queryFn: () =>
      getAdminVerifications({
        search: search || undefined,
        status: statusFilter || undefined,
        page,
        size: 15,
      }),
  });

  const approveMutation = useMutation({
    mutationFn: ({ userSkillId, reason, scoreOverride }) =>
      approveAdminVerification(userSkillId, reason, scoreOverride ? parseFloat(scoreOverride) : null),
    onSuccess: () => {
      addToast("Mentor skill verification approved", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "verification"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to approve verification", "error");
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ userSkillId, reason }) => rejectAdminVerification(userSkillId, reason),
    onSuccess: () => {
      addToast("Mentor skill verification rejected", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "verification"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to reject verification", "error");
    },
  });

  const closeModal = () => {
    setSelectedRecord(null);
    setModalMode(null);
    setReason("");
    setScoreOverride("");
  };

  const handleAction = (e) => {
    e.preventDefault();
    if (!reason.trim()) {
      addToast("A valid explanation reason is mandatory for the audit log.", "warning");
      return;
    }

    if (modalMode === "approve") {
      approveMutation.mutate({
        userSkillId: selectedRecord.id,
        reason,
        scoreOverride: scoreOverride || null,
      });
    } else {
      rejectMutation.mutate({
        userSkillId: selectedRecord.id,
        reason,
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Mentor & Skill Verifications</h1>
        <p className="text-sm text-slate-400">
          Review skill verification test attempts, approve credentials, and maintain mentor discovery integrity.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by user or skill name..."
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
            <option value="">All Verification Statuses</option>
            <option value="CLAIMED">Pending (Claimed)</option>
            <option value="VERIFIED">Verified</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3.5 px-4">Candidate</th>
                <th className="py-3.5 px-4">Skill Claimed</th>
                <th className="py-3.5 px-4">Test Score</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Claimed Date</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-500">
                    Loading verification records...
                  </td>
                </tr>
              ) : data?.items?.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-500">
                    No verification records found.
                  </td>
                </tr>
              ) : (
                data?.items?.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-100">{item.user_name}</div>
                      <div className="text-xs text-slate-400 font-mono">{item.user_email}</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="font-medium text-slate-200">{item.skill_name}</span>
                      <span className="text-xs text-slate-500 block">{item.skill_category}</span>
                    </td>

                    <td className="py-3.5 px-4 text-xs font-mono font-bold">
                      {item.score !== null ? (
                        <span className={item.score >= 80 ? "text-emerald-400" : "text-amber-400"}>
                          {item.score}%
                        </span>
                      ) : (
                        <span className="text-slate-500 font-normal">No test taken</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          item.verification_status === "VERIFIED"
                            ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
                            : item.verification_status === "REJECTED"
                            ? "bg-red-500/10 border border-red-500/30 text-red-300"
                            : "bg-amber-500/10 border border-amber-500/30 text-amber-300"
                        }`}
                      >
                        {item.verification_status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {item.claimed_at ? new Date(item.claimed_at).toLocaleDateString() : "—"}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => {
                            setSelectedRecord(item);
                            setScoreOverride(item.score ? String(item.score) : "90");
                            setModalMode("approve");
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                          title="Approve Verification"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedRecord(item);
                            setModalMode("reject");
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Reject Verification"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
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
            <strong className="text-slate-200">{data?.total_pages || 1}</strong> ({data?.total || 0} verifications)
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

      {/* Action Modal */}
      {selectedRecord && modalMode && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="max-w-md w-full rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100">
                {modalMode === "approve" ? "Approve Skill Verification" : "Reject Skill Verification"}
              </h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAction} className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-slate-400">Candidate: <strong className="text-slate-200">{selectedRecord.user_name}</strong></div>
                <div className="text-slate-400">Skill: <strong className="text-slate-200">{selectedRecord.skill_name}</strong></div>
              </div>

              {modalMode === "approve" && (
                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-300">Score / Grade Override (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={scoreOverride}
                    onChange={(e) => setScoreOverride(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Audit Reason / Verification Notes</label>
                <textarea
                  rows="3"
                  required
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Provide audit justification..."
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
                  className={`flex-1 py-2 rounded-xl font-semibold text-white ${
                    modalMode === "approve"
                      ? "bg-emerald-600 hover:bg-emerald-500"
                      : "bg-red-600 hover:bg-red-500"
                  }`}
                >
                  {modalMode === "approve" ? "Approve Verification" : "Reject Claim"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
