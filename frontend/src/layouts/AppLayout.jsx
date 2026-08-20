import React, { useState, useEffect } from "react";
import { Link, NavLink, useNavigate, Outlet, useLocation } from "react-router-dom";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../store/authStore";
import Avatar from "../components/common/Avatar";
import Footer from "../components/common/Footer";
import api from "../services/api";
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
  MessageSquare,
  Activity,
  Bot,
  Brain,
  FolderOpen,
  Sparkles,
  BookOpen
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
      queryClient.invalidateQueries(["notifications"]);
      queryClient.invalidateQueries(["notifications", "unread"]);
    },
  });

  // Mark all as read
  const markAllAsReadMutation = useMutation({
    mutationFn: async () => {
      await api.patch("/notifications/read-all");
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["notifications"]);
      queryClient.invalidateQueries(["notifications", "unread"]);
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
    { name: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
    { name: "AI Mentor", to: "/mentor", icon: Bot },
    { name: "Mentor Knowledge", to: "/mentor/knowledge", icon: BookOpen },
    { name: "Mentor Memory", to: "/mentor/memory", icon: Brain },
    { name: "Learning Journey", to: "/journey/roadmap", icon: Compass },
    { name: "Skill Gap", to: "/journey/skill-gap", icon: Target },
    { name: "Discover Mentors", to: "/mentors", icon: Users },
    { name: "Sessions", to: "/sessions", icon: Calendar },
    { name: "Wallet", to: "/wallet", icon: WalletIcon },
    { name: "Learning Activity", to: "/activity", icon: Activity },
    { name: "Profile Settings", to: "/profile", icon: Settings },
  ];


  return (
    <div className="min-h-screen bg-bg text-text flex flex-col transition-colors duration-200">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-bg border-b border-border flex items-center justify-between px-6 h-16 shrink-0 transition-colors duration-200">
        <div className="flex items-center gap-3">
          {/* Mobile Menu Toggle */}
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-1.5 rounded-md hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer"
            aria-label="Toggle Navigation Menu"
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-2 font-bold text-lg tracking-tight select-none">
            <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center text-white">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
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
            <span>Skill<span className="text-accent">Swap</span></span>
          </Link>
        </div>

        {/* Right Header actions */}
        <div className="flex items-center gap-4">
          {/* Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-colors"
            title={`Switch to ${theme === "light" ? "Dark" : "Light"} Mode`}
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              className="p-2 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text cursor-pointer transition-colors relative"
              title="Notifications"
              aria-expanded={isNotificationsOpen}
            >
              <Bell size={18} />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger animate-pulse" />
              )}
            </button>

            {isNotificationsOpen && (
              <>
                {/* Dropdown Overlay backdrop to close */}
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setIsNotificationsOpen(false)}
                />

                {/* Notifications Dropdown */}
                <div className="absolute right-0 mt-2 w-80 rounded-lg border border-border bg-bg shadow-md py-1.5 z-50 text-xs text-left animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-4 py-2 border-b border-border flex items-center justify-between">
                    <p className="font-semibold">Notifications</p>
                    <span className="text-[10px] text-accent font-semibold">{unreadCount} new</span>
                  </div>

                  <div className="max-h-80 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-4 text-center text-text-secondary text-xs">
                        No notifications
                      </div>
                    ) : (
                      notifications.map((notification) => (
                        <div
                          key={notification.id}
                          className={`p-3 hover:bg-bg-alt cursor-pointer border-b border-border ${notification.is_read ? 'opacity-60' : ''}`}
                          onClick={() => markAsReadMutation.mutate(notification.id)}
                        >
                          <div className="flex items-start gap-2">
                            <div className={`p-1.5 rounded mt-0.5 ${notification.is_read ? 'bg-bg-alt text-text-secondary' : 'bg-accent/10 text-accent'}`}>
                              <CheckCircle size={12} />
                            </div>
                            <div className="flex-1">
                              <p className="font-semibold text-text text-xs">{notification.message}</p>
                              <p className="text-[10px] text-text-secondary mt-1">
                                {new Date(notification.created_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="p-2 border-t border-border">
                    <button
                      type="button"
                      onClick={() => markAllAsReadMutation.mutate()}
                      disabled={unreadCount === 0}
                      className="w-full text-center text-xs font-semibold text-accent hover:text-accent-hover py-1 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Mark all as read
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Divider */}
          <div className="h-6 w-px bg-border hidden sm:block" />

          {/* User profile menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsUserDropdownOpen(!isUserDropdownOpen)}
              className="flex items-center gap-2.5 p-1 rounded-full hover:bg-bg-alt cursor-pointer transition-colors"
              aria-expanded={isUserDropdownOpen}
            >
              <Avatar src={user?.avatar_url} alt={user?.name || "User"} size="sm" />
              <span className="hidden sm:block text-xs font-semibold max-w-[120px] truncate">
                {user?.name || "Profile"}
              </span>
            </button>

            {isUserDropdownOpen && (
              <>
                {/* Dropdown Overlay backdrop to close */}
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setIsUserDropdownOpen(false)}
                />

                {/* Dropdown Menu */}
                <div className="absolute right-0 mt-2 w-48 rounded-lg border border-border bg-bg shadow-md py-1.5 z-50 text-xs text-left animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-4 py-2 border-b border-border">
                    <p className="font-semibold truncate">{user?.name}</p>
                    <p className="text-[10px] text-text-secondary truncate mt-0.5">{user?.email}</p>
                  </div>

                  <Link
                    to="/profile"
                    onClick={() => setIsUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-2 hover:bg-bg-alt text-text transition-colors"
                  >
                    <Settings size={14} className="text-text-secondary" />
                    Profile Settings
                  </Link>
                  <Link
                    to="/wallet"
                    onClick={() => setIsUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-2 hover:bg-bg-alt text-text transition-colors"
                  >
                    <WalletIcon size={14} className="text-text-secondary" />
                    Wallet Balance
                  </Link>

                  <div className="h-px bg-border my-1" />

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-4 py-2 hover:bg-danger/10 text-danger transition-colors cursor-pointer text-left font-medium"
                  >
                    <LogOut size={14} />
                    Sign Out
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Layout Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar Navigation */}
        <aside
          className={`hidden md:flex flex-col bg-bg border-r border-border gap-1.5 transition-all duration-300 ${
            isSidebarCollapsed ? "w-16 px-2 py-4" : "w-64 p-4"
          }`}
        >
          {/* Collapse Toggle Button */}
          <button
            type="button"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="flex items-center justify-center p-2 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text transition-colors mb-2 cursor-pointer"
            title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isSidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={18} />}
          </button>

          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl text-xs font-semibold transition-all duration-150 cursor-pointer ${
                  isActive
                    ? "bg-accent/15 text-accent border border-accent/20 shadow-xs"
                    : "text-text-secondary border border-transparent hover:bg-bg-alt hover:text-text"
                } ${isSidebarCollapsed ? "justify-center py-3 px-0 w-12 mx-auto" : "px-3 py-2.5"}`
              }
              title={isSidebarCollapsed ? item.name : undefined}
            >
              <item.icon size={isSidebarCollapsed ? 22 : 18} className="shrink-0" />
              {!isSidebarCollapsed && <span className="truncate">{item.name}</span>}
            </NavLink>
          ))}
        </aside>


        {/* Mobile Navigation Drawer Overlay */}
        {isMobileMenuOpen && (
          <>
            <div
              className="fixed inset-0 bg-black/30 backdrop-blur-xs z-30 md:hidden"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <aside className="fixed left-0 top-16 bottom-0 w-64 bg-bg border-r border-border p-4 flex flex-col gap-1.5 z-40 md:hidden animate-in slide-in-from-left duration-200">
              {navItems.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.to}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${isActive
                      ? "bg-accent/10 text-accent border border-accent/15"
                      : "text-text-secondary border border-transparent hover:bg-bg-alt hover:text-text"
                    }`
                  }
                >
                  <item.icon size={16} />
                  {item.name}
                </NavLink>
              ))}
            </aside>
          </>
        )}

        {/* Main Content Area */}
        <main className={`flex-1 overflow-y-auto bg-bg-alt transition-colors duration-200 ${
          isMentorWorkspace ? "p-2 sm:p-4" : "p-6 md:p-8"
        }`}>
          <div className={`${isMentorWorkspace ? "w-full h-full" : "max-w-6xl mx-auto pb-8"}`}>
            <Outlet />
          </div>
        </main>

      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
}
