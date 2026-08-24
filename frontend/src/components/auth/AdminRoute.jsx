import React from "react";
import { Navigate, Outlet, Link } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { ShieldAlert, ArrowLeft, Lock } from "lucide-react";

export default function AdminRoute() {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const role = (user?.role || "").toUpperCase();

  if (role !== "ADMIN") {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900/80 border border-red-500/20 rounded-2xl p-8 backdrop-blur-xl shadow-2xl text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto text-red-400">
            <Lock className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-slate-100">403 Forbidden</h1>
            <p className="text-slate-400 text-sm">
              Administrator privileges required. Your account (<span className="text-slate-200 font-mono">{user?.email}</span>) does not have access to the platform console.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/dashboard"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 text-sm font-medium transition-all duration-200 w-full"
            >
              <ArrowLeft className="w-4 h-4" />
              Return to User Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <Outlet />;
}
