import React from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import api from "../services/api";
import Card from "../components/common/Card";
import SectionHeader from "../components/common/SectionHeader";
import EmptyState from "../components/common/EmptyState";
import PageTransition from "../components/common/PageTransition";
import { PushPin } from "../components/common/PinnedCard";
import { MarkerHighlight, HandDrawnNote } from "../components/common/HandwrittenAnnotation";
import {
  Wallet as WalletIcon,
  ArrowUp,
  ArrowDown,
  History,
  Gift,
  ShieldCheck,
  Zap,
  TrendingUp,
  TrendingDown,
  Sparkles,
} from "lucide-react";

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
        return {
          label: "Welcome Bonus",
          color: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
          icon: <Gift size={16} />,
        };
      case "credit":
      case "earned":
        return {
          label: "Earned (Teaching)",
          color: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
          icon: <ArrowUp size={16} />,
        };
      case "debit":
      case "spent":
        return {
          label: "Spent (Learning)",
          color: "text-rose-500 bg-rose-500/10 border-rose-500/20",
          icon: <ArrowDown size={16} />,
        };
      case "bonus":
        return {
          label: "Platform Bonus",
          color: "text-accent bg-accent/10 border-accent/20",
          icon: <Gift size={16} />,
        };
      default:
        return {
          label: type || "Transaction",
          color: "text-text-secondary bg-surface-elevated border-border",
          icon: <History size={16} />,
        };
    }
  };

  return (
    <PageTransition className="space-y-8 text-left max-w-6xl mx-auto">
      {/* Section Header */}
      <SectionHeader
        badge="Skill Coin Economy"
        badgeIcon={WalletIcon}
        handwrittenNote="📌 Live Coin Ledger"
        title="Skill Coins Wallet"
        subtitle="Auditable internal credit ledger. Earn coins by teaching, spend coins to learn."
        actions={
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-xs font-bold shadow-xs">
            <ShieldCheck size={15} />
            <span>Verified Peer Ledger</span>
          </div>
        }
      />

      {/* Balance Hero Card with Pushpin */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-visible rounded-3xl bg-gradient-to-r from-accent via-indigo-600 to-purple-700 text-white p-6 sm:p-10 shadow-xl"
      >
        <PushPin color="yellow" className="-top-3 left-10" />

        {/* Hand-drawn badge */}
        <div className="absolute -top-3 right-8 font-handwriting text-sm font-bold text-amber-900 bg-yellow-200 px-3 py-0.5 rounded-lg border border-yellow-400 rotate-2 shadow-sm">
          Active Student Balance 📌
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10 pt-1">
          <div className="space-y-1">
            <p className="text-xs sm:text-sm font-bold text-white/80 uppercase tracking-wider">
              Available Skill Coins Balance
            </p>
            <div className="flex items-baseline gap-3">
              <span className="text-4xl sm:text-6xl font-black tracking-tight">
                {isWalletLoading ? "..." : wallet?.balance ?? "0"}
              </span>
              <span className="text-lg sm:text-xl font-extrabold text-white/90">
                Skill Coins
              </span>
            </div>
            <p className="text-xs text-white/70 pt-1 font-handwriting text-base">
              ✦ 1 Coin = 1 Peer Learning Credit
            </p>
          </div>

          <div className="p-5 bg-white/15 rounded-3xl backdrop-blur-md border border-white/25 shadow-lg w-fit">
            <WalletIcon size={48} className="text-white" />
          </div>
        </div>

        {/* Total stats breakdown */}
        <div className="mt-8 grid grid-cols-2 gap-4 relative z-10">
          <div className="bg-white/10 rounded-2xl p-4 backdrop-blur-xs border border-white/15">
            <div className="flex items-center gap-2 text-white/80 text-xs font-semibold">
              <TrendingUp size={14} className="text-emerald-300" />
              <span>Total Earned Coins</span>
            </div>
            <p className="text-2xl font-black text-white mt-1">
              +{isWalletLoading ? "..." : wallet?.earned_coins ?? "0"}
            </p>
          </div>
          <div className="bg-white/10 rounded-2xl p-4 backdrop-blur-xs border border-white/15">
            <div className="flex items-center gap-2 text-white/80 text-xs font-semibold">
              <TrendingDown size={14} className="text-rose-300" />
              <span>Total Spent Coins</span>
            </div>
            <p className="text-2xl font-black text-white mt-1">
              -{isWalletLoading ? "..." : wallet?.spent_coins ?? "0"}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Transaction History */}
      <Card
        title="Transaction History"
        subtitle="Auditable ledger entries of your peer teaching & learning activity"
      >
        {isTransactionsLoading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 w-full bg-border/40 animate-pulse rounded-2xl" />
            ))}
          </div>
        ) : transactions.length === 0 ? (
          <EmptyState
            icon={History}
            title="No transactions yet"
            description="Your Skill Coin balance ledger will record credits when you teach or spend coins for learning sessions."
          />
        ) : (
          <div className="divide-y divide-border/60">
            {transactions.map((tx) => {
              const meta = formatTransactionType(tx.transaction_type);
              const isPositive =
                tx.amount > 0 ||
                tx.transaction_type === "WELCOME_BONUS" ||
                tx.transaction_type === "credit" ||
                tx.transaction_type === "earned";

              return (
                <div
                  key={tx.id}
                  className="py-4 flex items-center justify-between gap-4 hover:bg-bg-alt/40 px-2 rounded-xl transition-colors"
                >
                  <div className="flex items-center gap-3.5">
                    <div className={`p-2.5 rounded-xl border ${meta.color}`}>
                      {meta.icon}
                    </div>
                    <div>
                      <h4 className="font-bold text-xs sm:text-sm text-text">
                        {meta.label}
                      </h4>
                      <p className="text-[11px] text-text-secondary mt-0.5">
                        {tx.description || "Peer Skill Swap Transaction"} •{" "}
                        {new Date(tx.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span
                      className={`text-sm sm:text-base font-black ${
                        isPositive
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-rose-500"
                      }`}
                    >
                      {isPositive ? `+${Math.abs(tx.amount)}` : `-${Math.abs(tx.amount)}`} Coins
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </PageTransition>
  );
}
