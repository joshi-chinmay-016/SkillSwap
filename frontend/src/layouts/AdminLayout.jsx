import React, { useState, useEffect } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import {
  LayoutDashboard,
  Users,
  Award,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  Coins,
  BarChart3,
  Server,
  FileText,
  Shield,
  ExternalLink,
  LogOut,
  Menu,
  X,
  Activity,
  ChevronRight
} from "lucide-react";
import { getAdminSystemHealth } from "../api/adminApi";

const NAV_ITEMS = [
  { path: "/admin", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { path: "/admin/users", label: "Users", icon: Users },
  { path: "/admin/skills", label: "Skills", icon: Award },
  { path: "/admin/verification", label: "Verifications", icon: CheckCircle2 },
  { path: "/admin/sessions", label: "Sessions", icon: Calendar },
  { path: "/admin/reports", label: "Moderation", icon: AlertTriangle },
  { path: "/admin/wallet", label: "Wallet & Coins", icon: Coins },
  { path: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { path: "/admin/system", label: "System Health", icon: Server },
  { path: "/admin/audit-logs", label: "Audit Logs", icon: FileText },
];

export default function AdminLayout() {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [systemHealth, setSystemHealth] = useState({ status: "healthy" });

  useEffect(() => {
    let isMounted = true;
    getAdminSystemHealth()
      .then((data) => {
        if (isMounted) setSystemHealth(data);
      })
      .catch(() => {
        if (isMounted) setSystemHealth({ status: "degraded" });
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const currentNav = NAV_ITEMS.find((item) =>
    item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path)
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Top Navbar */}
      <header className="h-16 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl sticky top-0 z-40 px-4 lg:px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
            aria-label="Toggle Sidebar"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <Link to="/admin" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold tracking-tight text-white">SkillSwap</span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 rounded">
                  Admin Console
                </span>
              </div>
            </div>
          </Link>

          {/* Breadcrumb */}
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 pl-4 border-l border-slate-800">
            <Link to="/admin" className="hover:text-slate-200 transition-colors">Admin</Link>
            {currentNav && currentNav.path !== "/admin" && (
              <>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                <span className="text-slate-200 font-medium">{currentNav.label}</span>
              </>
            )}
          </div>
        </div>

        {/* Right tools */}
        <div className="flex items-center gap-3">
          {/* Health indicator */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700/50 text-xs text-slate-300">
            <span className={`w-2 h-2 rounded-full ${systemHealth.status === "healthy" ? "bg-emerald-400 animate-pulse" : "bg-amber-400 animate-pulse"}`} />
            <span className="hidden sm:inline capitalize">{systemHealth.status}</span>
          </div>

          <Link
            to="/dashboard"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs font-medium text-slate-300 hover:text-white border border-slate-700 transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Go to App</span>
          </Link>

          {/* Admin user info & logout */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-300">
              {user?.name ? user.name.slice(0, 2).toUpperCase() : "AD"}
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Body container with Sidebar & Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`fixed lg:static inset-y-16 left-0 z-30 w-64 bg-slate-900/90 lg:bg-slate-900/40 border-r border-slate-800/80 backdrop-blur-xl flex flex-col justify-between transform transition-transform duration-300 ease-in-out ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
          }`}
        >
          <div className="p-4 space-y-1 overflow-y-auto">
            <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Navigation
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = item.exact
                ? location.pathname === item.path
                : location.pathname.startsWith(item.path);

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20 font-semibold"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
                  {item.label}
                </NavLink>
              );
            })}
          </div>

          {/* Sidebar bottom */}
          <div className="p-4 border-t border-slate-800/60 bg-slate-950/40">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-mono text-indigo-400 border border-slate-700">
                8.0
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-200">Phase 8 Platform</div>
                <div className="text-[10px] text-slate-500">GCP & Production RBAC</div>
              </div>
            </div>
          </div>
        </aside>

        {/* Mobile backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/60 z-20 lg:hidden backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main page content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
          <div className="max-w-7xl mx-auto space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
