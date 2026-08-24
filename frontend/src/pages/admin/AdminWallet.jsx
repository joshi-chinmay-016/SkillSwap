import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Coins,
  Search,
  Plus,
  Minus,
  TrendingUp,
  CreditCard,
  X,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { getAdminWallet, adjustAdminWallet } from "../../api/adminApi";
import { useToast } from "../../components/common/Toast";

export default function AdminWallet() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [targetUserId, setTargetUserId] = useState("");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "wallet", page],
    queryFn: () => getAdminWallet({ page, size: 20 }),
  });

  const adjustMutation = useMutation({
    mutationFn: adjustAdminWallet,
    onSuccess: (res) => {
      addToast(res.message || "Wallet balance adjusted", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "wallet"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to adjust wallet", "error");
    },
  });

  const closeModal = () => {
    setModalOpen(false);
    setTargetUserId("");
    setAmount("");
    setReason("");
  };

  const handleAdjustSubmit = (e) => {
    e.preventDefault();
    const parsedUserId = parseInt(targetUserId, 10);
    const parsedAmount = parseInt(amount, 10);

    if (isNaN(parsedUserId) || isNaN(parsedAmount) || parsedAmount === 0) {
      addToast("Please provide a valid User ID and non-zero coin amount.", "warning");
      return;
    }
    if (!reason.trim()) {
      addToast("A mandatory explanation reason is required for the audit log.", "warning");
      return;
    }

    adjustMutation.mutate({
      target_user_id: parsedUserId,
      amount: parsedAmount,
      reason,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Wallet & Economy Oversight</h1>
          <p className="text-sm text-slate-400">
            Monitor coin transactions, circulating supply, and make audited administrative balance adjustments.
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition-all"
        >
          <Coins className="w-4 h-4" />
          Adjust User Balance
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Total Circulating Coins
          </div>
          <div className="text-3xl font-bold text-amber-400 flex items-center gap-2">
            {data?.total_circulation || 0} <span>🪙</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Total Historical Transactions
          </div>
          <div className="text-3xl font-bold text-slate-200">
            {data?.total_transactions || 0}
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-950/40 text-xs font-semibold text-slate-300">
          Recent Economy Transactions
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3.5 px-4">TX ID</th>
                <th className="py-3.5 px-4">Account</th>
                <th className="py-3.5 px-4">Type</th>
                <th className="py-3.5 px-4">Amount</th>
                <th className="py-3.5 px-4">Reason / Description</th>
                <th className="py-3.5 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-500">
                    Loading transactions...
                  </td>
                </tr>
              ) : data?.items?.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-500">
                    No transactions recorded.
                  </td>
                </tr>
              ) : (
                data?.items?.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      #{tx.id}
                    </td>

                    <td className="py-3.5 px-4 text-xs">
                      <div className="font-semibold text-slate-200">{tx.user_name}</div>
                      <div className="text-slate-500 font-mono">{tx.user_email}</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                        {tx.type}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-xs font-bold">
                      <span className={tx.amount > 0 ? "text-emerald-400" : "text-red-400"}>
                        {tx.amount > 0 ? `+${tx.amount}` : tx.amount} 🪙
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-300">
                      {tx.reason}
                    </td>

                    <td className="py-3.5 px-4 text-xs text-slate-400 text-right">
                      {tx.created_at ? new Date(tx.created_at).toLocaleString() : "—"}
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
            <strong className="text-slate-200">{data?.total_pages || 1}</strong> ({data?.total_transactions || 0} total)
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

      {/* Adjust Balance Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="max-w-md w-full rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100">Adjust User Coin Balance</h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAdjustSubmit} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Target User ID</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 42"
                  value={targetUserId}
                  onChange={(e) => setTargetUserId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Amount (+ for reward, - for deduction)</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 5 or -2"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-300">Mandatory Audit Reason</label>
                <textarea
                  rows="3"
                  required
                  placeholder="Explain why this balance adjustment is being made..."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
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
                  className="flex-1 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-lg shadow-amber-500/20"
                >
                  Execute Adjustment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
