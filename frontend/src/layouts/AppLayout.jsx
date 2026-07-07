import React, { useState, useEffect } from "react";
import { Link, NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import Avatar from "../components/common/Avatar";
import Footer from "../components/common/Footer";
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
  Target
} from "lucide-react";

export default function AppLayout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

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
    { name: "Learning Journey", to: "/journey/roadmap", icon: Compass },
    { name: "Skill Gap", to: "/journey/skill-gap", icon: Target },
    { name: "Discover Mentors", to: "/mentors", icon: Users },
    { name: "Sessions", to: "/sessions", icon: Calendar },
    { name: "AI Chat", to: "/ai/chat", icon: Bell },
    { name: "Wallet", to: "/wallet", icon: WalletIcon },
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
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger animate-pulse" />
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
                    <span className="text-[10px] text-accent font-semibold">3 new</span>
                  </div>
                  
                  <div className="max-h-80 overflow-y-auto">
                    <div className="p-3 hover:bg-bg-alt cursor-pointer border-b border-border">
                      <div className="flex items-start gap-2">
                        <div className="p-1.5 bg-success/10 text-success rounded mt-0.5">
                          <Calendar size={12} />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-text text-xs">Session Reminder</p>
                          <p className="text-[10px] text-text-secondary mt-0.5">
                            Your React mentoring session starts in 30 minutes
                          </p>
                          <p className="text-[10px] text-text-secondary mt-1">2 minutes ago</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 hover:bg-bg-alt cursor-pointer border-b border-border">
                      <div className="flex items-start gap-2">
                        <div className="p-1.5 bg-accent/10 text-accent rounded mt-0.5">
                          <WalletIcon size={12} />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-text text-xs">Coins Earned</p>
                          <p className="text-[10px] text-text-secondary mt-0.5">
                            You earned 5 Skill Coins for teaching a session
                          </p>
                          <p className="text-[10px] text-text-secondary mt-1">1 hour ago</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 hover:bg-bg-alt cursor-pointer border-b border-border">
                      <div className="flex items-start gap-2">
                        <div className="p-1.5 bg-warning/10 text-warning rounded mt-0.5">
                          <Users size={12} />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-text text-xs">New Mentor Match</p>
                          <p className="text-[10px] text-text-secondary mt-0.5">
                            We found 3 new mentors matching your learning goals
                          </p>
                          <p className="text-[10px] text-text-secondary mt-1">3 hours ago</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 hover:bg-bg-alt cursor-pointer opacity-60">
                      <div className="flex items-start gap-2">
                        <div className="p-1.5 bg-bg-alt text-text-secondary rounded mt-0.5">
                          <CheckCircle size={12} />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-text text-xs">Profile Updated</p>
                          <p className="text-[10px] text-text-secondary mt-0.5">
                            Your profile was successfully updated
                          </p>
                          <p className="text-[10px] text-text-secondary mt-1">Yesterday</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-2 border-t border-border">
                    <button
                      type="button"
                      className="w-full text-center text-xs font-semibold text-accent hover:text-accent-hover py-1"
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
          className={`hidden md:flex flex-col bg-bg border-r border-border p-4 gap-1.5 transition-all duration-300 ${
            isSidebarCollapsed ? 'w-16' : 'w-64'
          }`}
        >
          {/* Collapse Toggle Button */}
          <button
            type="button"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="flex items-center justify-center p-2 rounded-lg hover:bg-bg-alt text-text-secondary hover:text-text transition-colors mb-2"
            title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isSidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>

          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${
                  isActive
                    ? "bg-accent/10 text-accent border border-accent/15"
                    : "text-text-secondary border border-transparent hover:bg-bg-alt hover:text-text"
                } ${isSidebarCollapsed ? 'justify-center' : ''}`
              }
              title={isSidebarCollapsed ? item.name : undefined}
            >
              <item.icon size={16} />
              {!isSidebarCollapsed && <span>{item.name}</span>}
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
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${
                      isActive
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
        <main className="flex-1 overflow-y-auto bg-bg-alt p-6 md:p-8 transition-colors duration-200">
          <div className="max-w-6xl mx-auto pb-8">
            <Outlet />
          </div>
        </main>
      </div>
      
      {/* Footer */}
      <Footer />
    </div>
  );
}
