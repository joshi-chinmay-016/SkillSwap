import React from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api";
import Card from "../components/common/Card";
import { Wallet as WalletIcon, ArrowUp, ArrowDown, History, Gift, ShieldCheck } from "lucide-react";

export default function Wallet() {
  const { data: wallet, isLoading: isWalletLoading } = useQuery({
    queryKey: ["wallet"],
    queryFn: async () => {
      const res = await api.get("/wallet/me");
      return res.data;
    },
    retry: false,
  });

  const { data: transactions = [], isLoading: isTransactionsLoading } = useQuery({
    queryKey: ["transactions"],
    queryFn: async () => {
      const res = await api.get("/wallet/transactions");
      return res.data;
    },
    retry: false,
  });

  const formatTransactionType = (type) => {
    switch (type) {
      case "WELCOME_BONUS":
        return { label: "Welcome Bonus", color: "text-emerald-500", icon: <Gift size={16} /> };
      case "credit":
      case "earned":
        return { label: "Earned Credit", color: "text-emerald-500", icon: <ArrowUp size={16} /> };
      case "debit":
      case "spent":
        return { label: "Spent Credit", color: "text-rose-500", icon: <ArrowDown size={16} /> };
      case "bonus":
        return { label: "Bonus", color: "text-accent", icon: <Gift size={16} /> };
      default:
        return { label: type, color: "text-text-secondary", icon: <History size={16} /> };
    }
  };

  return (
    <div className="flex flex-col gap-6 text-left">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Skill Coins Wallet</h1>
          <p className="text-sm text-text-secondary mt-1">
            Internal platform credit ledger & transaction history
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-xs font-bold">
          <ShieldCheck size={14} /> Auditable Ledger
        </div>
      </div>

      {/* Balance Card */}
      <Card className="bg-gradient-to-br from-accent to-accent-hover text-white border-0 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white/80">Current Skill Coins Balance</p>
            <p className="text-4xl font-extrabold mt-2 tracking-tight">
              {isWalletLoading ? "..." : (wallet?.balance ?? "0")}
              <span className="text-lg font-semibold text-white/80 ml-2">Coins</span>
            </p>
          </div>
          <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md">
            <WalletIcon size={48} className="text-white" />
          </div>
        </div>
        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
            <p className="text-xs text-white/70">Total Earned Coins</p>
            <p className="text-lg font-extrabold">
              {isWalletLoading ? "..." : (wallet?.earned_coins ?? "0")}
            </p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
            <p className="text-xs text-white/70">Total Spent Coins</p>
            <p className="text-lg font-extrabold">
              {isWalletLoading ? "..." : (wallet?.spent_coins ?? "0")}
            </p>
          </div>
        </div>
      </Card>

      {/* Transaction History */}
      <Card title="Transaction History" subtitle="Auditable ledger entries of your Skill Coin activity">
        {isTransactionsLoading ? (
          <div className="flex flex-col gap-3 py-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 w-full bg-border/40 animate-pulse rounded-lg" />
            ))}
          </div>
        ) : transactions.length === 0 ? (
          <div className="py-12 text-center">
            <div className="w-12 h-12 rounded-full bg-bg-alt flex items-center justify-center text-text-secondary border border-border mx-auto mb-3">
              <History size={24} />
            </div>
            <p className="font-semibold text-sm">No transactions yet</p>
            <p className="text-xs text-text-secondary mt-1">
              Your welcome bonus and session transactions will appear here.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-2.5">
            {transactions.map((txn) => {
              const { label, color, icon } = formatTransactionType(txn.type);
              const isPositive =
                txn.type === "earned" ||
                txn.type === "bonus" ||
                txn.type === "credit" ||
                txn.type === "WELCOME_BONUS";

              return (
                <div
                  key={txn.id}
                  className="flex items-center justify-between p-4 bg-bg border border-border rounded-xl hover:border-accent/30 transition-colors shadow-xs"
                >
                  <div className="flex items-center gap-3.5">
                    <div
                      className={`p-2.5 rounded-xl ${
                        isPositive ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      {icon}
                    </div>
                    <div>
                      <p className="font-bold text-sm text-text">{txn.reason}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={`text-xs font-semibold ${color}`}>{label}</span>
                        {txn.created_at && (
                          <span className="text-[11px] text-text-secondary">
                            • {new Date(txn.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p
                      className={`font-black text-base ${
                        isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-red-500"
                      }`}
                    >
                      {isPositive ? "+" : "-"}{txn.amount}
                    </p>
                    <p className="text-[11px] text-text-secondary font-medium">Coins</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* How it Works */}
      <Card title="Skill Coin Economy" subtitle="Internal peer-learning credits">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-bg border border-border rounded-xl">
            <div className="p-2 bg-emerald-500/10 text-emerald-500 rounded-lg w-fit mb-3">
              <Gift size={20} />
            </div>
            <h3 className="font-bold text-sm text-text mb-1">5 Welcome Coins</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Every genuinely new student registration receives 5 free platform coins to start booking peer sessions.
            </p>
          </div>
          <div className="p-4 bg-bg border border-border rounded-xl">
            <div className="p-2 bg-emerald-500/10 text-emerald-500 rounded-lg w-fit mb-3">
              <ArrowUp size={20} />
            </div>
            <h3 className="font-bold text-sm text-text mb-1">Earn by Teaching</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Host peer learning sessions and share your verified skills to earn internal platform credits.
            </p>
          </div>
          <div className="p-4 bg-bg border border-border rounded-xl">
            <div className="p-2 bg-rose-500/10 text-rose-500 rounded-lg w-fit mb-3">
              <ArrowDown size={20} />
            </div>
            <h3 className="font-bold text-sm text-text mb-1">Spend by Learning</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Use your accumulated Skill Coins to book 1-on-1 sessions with top verified mentors.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
