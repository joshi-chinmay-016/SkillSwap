import React from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import { Wallet as WalletIcon, ArrowUp, ArrowDown, History, Plus, Gift } from "lucide-react";

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
      case "earned":
        return { label: "Earned", color: "text-success", icon: <ArrowUp size={16} /> };
      case "spent":
        return { label: "Spent", color: "text-danger", icon: <ArrowDown size={16} /> };
      case "bonus":
        return { label: "Bonus", color: "text-accent", icon: <Gift size={16} /> };
      default:
        return { label: type, color: "text-text-secondary", icon: <History size={16} /> };
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Skill Coins Wallet</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage your Skill Coins and view transaction history
          </p>
        </div>
        <Button variant="primary" size="sm">
          <Plus size={16} className="mr-2" />
          Buy Coins
        </Button>
      </div>

      {/* Balance Card */}
      <Card className="bg-gradient-to-br from-accent to-accent-hover text-white border-0">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white/80">Current Balance</p>
            <p className="text-4xl font-bold mt-2">
              {isWalletLoading ? "..." : (wallet?.balance ?? "—")}
              <span className="text-lg font-semibold text-white/70 ml-2">Coins</span>
            </p>
          </div>
          <div className="p-4 bg-white/10 rounded-2xl">
            <WalletIcon size={48} className="text-white" />
          </div>
        </div>
          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-xs text-white/70">Total Earned</p>
              <p className="text-lg font-semibold">
                {isWalletLoading ? "..." : (wallet?.earned_coins ?? "—")}
              </p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-xs text-white/70">Total Spent</p>
              <p className="text-lg font-semibold">
                {isWalletLoading ? "..." : (wallet?.spent_coins ?? "—")}
              </p>
            </div>
          </div>
      </Card>

      {/* Transaction History */}
      <Card title="Transaction History" subtitle="Your recent Skill Coin activity">
        {isTransactionsLoading ? (
          <div className="flex flex-col gap-3 py-4">
            {[1, 2, 3, 4].map((i) => (
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
              Start teaching or booking sessions to see your activity here.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {transactions.map((txn) => {
              const { label, color, icon } = formatTransactionType(txn.type);
              const isPositive = txn.type === "earned" || txn.type === "bonus";
              
              return (
                <div
                  key={txn.id}
                  className="flex items-center justify-between p-4 bg-bg border border-border rounded-lg hover:border-accent/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${isPositive ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                      {icon}
                    </div>
                    <div>
                      <p className="font-semibold text-sm text-text">{txn.reason}</p>
                      <p className={`text-xs mt-0.5 ${color}`}>{label}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-bold text-sm ${isPositive ? "text-success" : "text-danger"}`}>
                      {isPositive ? "+" : "-"}{txn.amount}
                    </p>
                    <p className="text-xs text-text-secondary">Coins</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* How it Works */}
      <Card title="How Skill Coins Work" subtitle="Understanding the reward system">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-bg border border-border rounded-lg">
            <div className="p-2 bg-success/10 text-success rounded-lg w-fit mb-3">
              <ArrowUp size={20} />
            </div>
            <h3 className="font-semibold text-sm text-text mb-1">Earn Coins</h3>
            <p className="text-xs text-text-secondary">
              Teach a session and earn 5 Skill Coins for sharing your knowledge.
            </p>
          </div>
          <div className="p-4 bg-bg border border-border rounded-lg">
            <div className="p-2 bg-danger/10 text-danger rounded-lg w-fit mb-3">
              <ArrowDown size={20} />
            </div>
            <h3 className="font-semibold text-sm text-text mb-1">Spend Coins</h3>
            <p className="text-xs text-text-secondary">
              Book a mentoring session with any peer mentor for 5 Skill Coins.
            </p>
          </div>
          <div className="p-4 bg-bg border border-border rounded-lg">
            <div className="p-2 bg-accent/10 text-accent rounded-lg w-fit mb-3">
              <Gift size={20} />
            </div>
            <h3 className="font-semibold text-sm text-text mb-1">Get Bonuses</h3>
            <p className="text-xs text-text-secondary">
              Receive bonus coins for completing your profile and onboarding.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
