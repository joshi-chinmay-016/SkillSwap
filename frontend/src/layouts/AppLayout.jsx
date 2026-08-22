import React, { useState, useEffect } from "react";
import { Link, NavLink, useNavigate, Outlet, useLocation } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "motion/react";
import { useAuthStore } from "../store/authStore";
import Avatar from "../components/common/Avatar";
import Footer from "../components/common/Footer";
import api from "../services/api";
import { useWebSocket } from "../hooks/useWebSocket";
import {
  LayoutDashboard,
  Users,
  Calendar,
  Compass,
  Wallet as WalletIcon,
  Settings,
  LogOut,
  Bell,
  Sun,
  Moon,
  Menu,
  X,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Target,
  Activity,
  Bot,
  Brain,
  BookOpen,
  Sparkles,
  Search,
  ExternalLink,
} from "lucide-react";

export default function AppLayout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const queryClient = useQueryClient();

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();
  const location = useLocation();

  const isMentorWorkspace = location.pathname.startsWith("/mentor");

  // Mount real-time WebSocket connection for live session and notification events
  useWebSocket();

  // Fetch notifications
  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const res = await api.get("/notifications");
      return res.data;
    },
  });

  // Fetch unread count
  const { data: unreadData } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: async () => {
      const res = await api.get("/notifications/unread/count");
      return res.data;
    },
  });

  const unreadCount = unreadData?.count || 0;

  // Mark notification as read
  const markAsReadMutation = useMutation({
    mutationFn: async (notificationId) => {
      await api.patch(`/notifications/${notificationId}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
    },
  });

  // Mark all as read
  const markAllAsReadMutation = useMutation({
    mutationFn: async () => {
      await api.patch("/notifications/read-all");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
    },
  });

  // Apply theme to document element
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
    } else {
      root.classList.add("light");
      root.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Persist sidebar collapsed state
  useEffect(() => {
    const saved = localStorage.getItem("sidebarCollapsed");
    if (saved !== null) {
      setIsSidebarCollapsed(saved === "true");
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("sidebarCollapsed", isSidebarCollapsed);
  }, [isSidebarCollapsed]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { name: "Dashboard", to: "/dashboard", icon: LayoutDashboard, badge: null },
    { name: "AI Mentor", to: "/mentor", icon: Bot, badge: "AI" },
    { name: "Mentor Knowledge", to: "/mentor/knowledge", icon: BookOpen, badge: null },
    { name: "Mentor Memory", to: "/mentor/memory", icon: Brain, badge: null },
    { name: "Learning Roadmap", to: "/journey/roadmap", icon: Compass, badge: null },
    { name: "Skill Gap", to: "/journey/skill-gap", icon: Target, badge: null },
    { name: "Discover Mentors", to: "/mentors", icon: Users, badge: null },
    { name: "Sessions", to: "/sessions", icon: Calendar, badge: null },
    { name: "Skill Coins Wallet", to: "/wallet", icon: WalletIcon, badge: null },
    { name: "Learning Activity", to: "/activity", icon: Activity, badge: null },
    { name: "Profile & Badges", to: "/profile", icon: Settings, badge: null },
  ];

  return (
    <div className="min-h-screen whiteboard-grid text-text flex flex-col transition-colors duration-200 selection:bg-yellow-200 selection:text-slate-900">
      {/* Top Glass Header */}
      <header className="sticky top-0 z-40 glass-panel border-b border-border/80 flex items-center justify-between px-4 sm:px-6 h-16 shrink-0 transition-colors duration-200 shadow-xs">
        <div className="flex items-center gap-3">
          {/* Mobile Menu Toggle */}
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-xl hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-colors border border-transparent hover:border-border"
            aria-label="Toggle Navigation Menu"
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          {/* Logo */}
          <Link
            to="/dashboard"
            className="flex items-center gap-2.5 font-bold text-lg tracking-tight select-none group"
          >
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center text-white shadow-md group-hover:rotate-6 transition-transform duration-200">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4.5 w-4.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2.5"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                />
              </svg>
            </div>
            <span className="font-black text-lg tracking-tight text-text">
              Skill<span className="text-accent">Swap</span>{" "}
              <span className="font-handwriting text-base font-bold text-rose-500 rotate-[-4deg] inline-block ml-1">
                Arena 📌
              </span>
            </span>
          </Link>
        </div>

        {/* Right Header Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Quick AI Mentor Button */}
          <Link
            to="/mentor"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-accent/10 hover:bg-accent/20 border border-accent/25 text-accent text-xs font-semibold transition-all duration-200 hover:shadow-xs"
          >
            <Sparkles size={13} />
            <span>AI Mentor</span>
          </Link>

          {/* Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="p-2 rounded-xl hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-all duration-200 border border-transparent hover:border-border"
            title={`Switch to ${theme === "light" ? "Dark" : "Light"} Mode`}
          >
            {theme === "light" ? (
              <Moon size={18} className="transition-transform hover:-rotate-12" />
            ) : (
              <Sun size={18} className="text-amber-400 transition-transform hover:rotate-45" />
            )}
          </button>

          {/* Notifications Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              className="p-2 rounded-xl hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-all duration-200 relative border border-transparent hover:border-border"
              title="Notifications"
              aria-expanded={isNotificationsOpen}
            >
              <Bell size={18} />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-danger ring-2 ring-bg animate-pulse" />
              )}
            </button>

            <AnimatePresence>
              {isNotificationsOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsNotificationsOpen(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 10 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-[340px] sm:w-[420px] rounded-2xl border border-card-border bg-card-bg shadow-2xl py-2 z-50 text-xs text-left backdrop-blur-xl"
                  >
                    <div className="px-5 py-3.5 border-b border-border/80 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-text text-sm">Notifications</span>
                        {unreadCount > 0 && (
                          <span className="px-2.5 py-0.5 rounded-full bg-accent/15 text-accent text-[11px] font-bold">
                            {unreadCount} new
                          </span>
                        )}
                      </div>
                      <span className="font-handwriting text-base font-bold text-rose-500 rotate-[-2deg]">
                        Inbox 📌
                      </span>
                    </div>

                    <div className="max-h-96 overflow-y-auto divide-y divide-border/60">
                      {notifications.length === 0 ? (
                        <div className="p-10 text-center text-text-secondary text-xs space-y-2">
                          <Bell size={28} className="mx-auto text-text-muted opacity-40" />
                          <p className="font-semibold text-text">All caught up!</p>
                          <p className="text-[11px] text-text-muted">No new alerts or session requests.</p>
                        </div>
                      ) : (
                        notifications.map((notification) => {
                          const dateObj = notification.created_at ? new Date(notification.created_at) : null;
                          const isValidDate = dateObj && !isNaN(dateObj.getTime());
                          const formattedDate = isValidDate
                            ? `${dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} • ${dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                            : "Just now";

                          const isBooked = notification.type === "SESSION_BOOKED";
                          const isCancelled = notification.type === "SESSION_CANCELLED";
                          const isCompleted = notification.type === "SESSION_COMPLETED";

                          return (
                            <div
                              key={notification.id}
                              className={`p-4 hover:bg-bg-alt/80 cursor-pointer transition-colors ${
                                notification.is_read ? "opacity-60" : "bg-accent/5"
                              }`}
                              onClick={() => {
                                if (!notification.is_read) {
                                  markAsReadMutation.mutate(notification.id);
                                }
                                if (notification.related_session_id || isBooked || isCancelled || isCompleted) {
                                  setIsNotificationsOpen(false);
                                  navigate("/sessions");
                                }
                              }}
                            >
                              <div className="flex items-start gap-3">
                                <div
                                  className={`p-2 rounded-xl mt-0.5 shrink-0 ${
                                    isCancelled
                                      ? "bg-danger/15 text-danger"
                                      : isCompleted
                                      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                                      : isBooked
                                      ? "bg-accent/15 text-accent"
                                      : notification.is_read
                                      ? "bg-bg-alt text-text-secondary"
                                      : "bg-accent/15 text-accent"
                                  }`}
                                >
                                  {isBooked ? (
                                    <Calendar size={15} />
                                  ) : isCancelled ? (
                                    <X size={15} />
                                  ) : isCompleted ? (
                                    <CheckCircle size={15} />
                                  ) : (
                                    <Bell size={15} />
                                  )}
                                </div>
                                <div className="flex-1 min-w-0 space-y-1">
                                  {notification.title && (
                                    <p className="font-bold text-text text-xs tracking-tight">
                                      {notification.title}
                                    </p>
                                  )}
                                  <p className="font-medium text-text text-xs leading-relaxed">
                                    {notification.message}
                                  </p>
                                  <p className="text-[10px] text-text-muted font-medium">
                                    {formattedDate}
                                  </p>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      )}

                    </div>

                    <div className="p-3 border-t border-border/80 bg-bg-alt/40">
                      <button
                        type="button"
                        onClick={() => markAllAsReadMutation.mutate()}
                        disabled={unreadCount === 0}
                        className="w-full text-center text-xs font-bold text-accent hover:text-accent-hover py-2 rounded-xl hover:bg-accent/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                      >
                        Mark all as read
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          {/* Divider */}
          <div className="h-6 w-px bg-border hidden sm:block mx-1" />

          {/* User Profile Menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsUserDropdownOpen(!isUserDropdownOpen)}
              className="flex items-center gap-2.5 p-1 rounded-full hover:bg-bg-alt cursor-pointer transition-all duration-200 border border-transparent hover:border-border"
              aria-expanded={isUserDropdownOpen}
            >
              <Avatar src={user?.avatar_url} alt={user?.name || "User"} size="sm" />
              <span className="hidden sm:block text-xs font-semibold max-w-[110px] truncate text-text">
                {user?.name || "Profile"}
              </span>
            </button>

            <AnimatePresence>
              {isUserDropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsUserDropdownOpen(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 10 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-56 rounded-2xl border border-card-border bg-card-bg shadow-xl py-2 z-50 text-xs text-left backdrop-blur-xl"
                  >
                    <div className="px-4 py-3 border-b border-border">
                      <p className="font-semibold text-text text-sm truncate">{user?.name || "User"}</p>
                      <p className="text-[11px] text-text-secondary truncate mt-0.5">{user?.email}</p>
                    </div>

                    <div className="p-1 space-y-0.5">
                      <Link
                        to="/profile"
                        onClick={() => setIsUserDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-bg-alt text-text transition-colors"
                      >
                        <Settings size={14} className="text-text-secondary" />
                        <span>Profile & Badges</span>
                      </Link>
                      <Link
                        to="/wallet"
                        onClick={() => setIsUserDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-bg-alt text-text transition-colors"
                      >
                        <WalletIcon size={14} className="text-text-secondary" />
                        <span>Skill Coins Wallet</span>
                      </Link>
                    </div>

                    <div className="h-px bg-border my-1" />

                    <div className="p-1">
                      <button
                        type="button"
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-danger/10 text-danger transition-colors cursor-pointer text-left font-medium"
                      >
                        <LogOut size={14} />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      {/* Main Layout Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar Navigation */}
        <aside
          className={`hidden md:flex flex-col bg-bg/95 backdrop-blur-md border-r border-border/80 gap-1.5 transition-all duration-300 ${
            isSidebarCollapsed ? "w-18 px-2 py-4" : "w-64 p-4"
          }`}
        >
          {/* Collapse Toggle Button */}
          <button
            type="button"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="flex items-center justify-center p-2 rounded-xl hover:bg-bg-alt text-text-secondary hover:text-text transition-all duration-200 mb-2 cursor-pointer border border-transparent hover:border-border"
            title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isSidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>

          {/* Navigation Links */}
          <nav className="flex-1 space-y-1 overflow-y-auto pr-0.5">
            {navItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl text-xs font-semibold transition-all duration-180 cursor-pointer group relative ${
                    isActive
                      ? "bg-accent text-white shadow-glow"
                      : "text-text-secondary hover:bg-bg-alt hover:text-text"
                  } ${isSidebarCollapsed ? "justify-center py-3 px-0 w-12 mx-auto" : "px-3.5 py-2.5"}`
                }
                title={isSidebarCollapsed ? item.name : undefined}
              >
                {({ isActive }) => (
                  <>
                    <item.icon
                      size={isSidebarCollapsed ? 20 : 17}
                      className={`shrink-0 transition-transform group-hover:scale-110 ${
                        isActive ? "text-white" : "text-text-secondary group-hover:text-accent"
                      }`}
                    />
                    {!isSidebarCollapsed && (
                      <span className="truncate flex-1">{item.name}</span>
                    )}
                    {!isSidebarCollapsed && item.badge && (
                      <span
                        className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full ${
                          isActive
                            ? "bg-white/20 text-white"
                            : "bg-accent/15 text-accent"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Mobile Navigation Drawer */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-xs z-40 md:hidden"
                onClick={() => setIsMobileMenuOpen(false)}
              />
              <motion.aside
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="fixed left-0 top-0 bottom-0 w-72 bg-bg border-r border-border p-5 flex flex-col gap-2 z-50 md:hidden overflow-y-auto"
              >
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center text-white shadow-glow">
                      <Sparkles size={16} />
                    </div>
                    <span className="font-bold text-base">Skill<span className="text-accent">Swap</span></span>
                  </div>
                  <button
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="p-1.5 rounded-lg hover:bg-bg-alt text-text-secondary"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div className="space-y-1">
                  {navItems.map((item) => (
                    <NavLink
                      key={item.name}
                      to={item.to}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
                          isActive
                            ? "bg-accent text-white shadow-glow"
                            : "text-text-secondary hover:bg-bg-alt hover:text-text"
                        }`
                      }
                    >
                      <div className="flex items-center gap-3">
                        <item.icon size={17} />
                        <span>{item.name}</span>
                      </div>
                      {item.badge && (
                        <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded-full bg-accent/20 text-accent">
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  ))}
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <main
          className={`flex-1 transition-colors duration-200 ${
            isMentorWorkspace
              ? "p-1.5 sm:p-2.5 flex flex-col h-[calc(100vh-4rem)] overflow-hidden bg-bg-alt/20"
              : "overflow-y-auto bg-bg-alt/40 flex flex-col min-h-0"
          }`}
        >
          {isMentorWorkspace ? (
            <div className="w-full h-full flex flex-col min-h-0">
              <Outlet />
            </div>
          ) : (
            <div className="flex-1 flex flex-col min-h-full justify-between">
              <div className="flex-1 p-4 sm:p-6 md:p-8 max-w-7xl w-full mx-auto pb-10">
                <Outlet />
              </div>
              <Footer />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
