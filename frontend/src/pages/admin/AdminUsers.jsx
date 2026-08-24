import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users,
  Search,
  Filter,
  Shield,
  UserCheck,
  UserX,
  Eye,
  Coins,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  X,
  Check,
  Award
} from "lucide-react";
import { getAdminUsers, suspendAdminUser, reactivateAdminUser, updateAdminUserRole } from "../../api/adminApi";
import { useToast } from "../../components/common/Toast";

export default function AdminUsers() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState("");
  const [page, setPage] = useState(1);

  // Modals state
  const [selectedUser, setSelectedUser] = useState(null);
  const [actionType, setActionType] = useState(null); // 'suspend' | 'reactivate' | 'role' | 'detail'
  const [reason, setReason] = useState("");
  const [targetRole, setTargetRole] = useState("ADMIN");

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin", "users", search, roleFilter, activeFilter, page],
    queryFn: () =>
      getAdminUsers({
        search: search || undefined,
        role: roleFilter || undefined,
        is_active: activeFilter === "" ? undefined : activeFilter === "true",
        page,
        size: 15,
      }),
  });

  const suspendMutation = useMutation({
    mutationFn: ({ userId, reason }) => suspendAdminUser(userId, reason),
    onSuccess: (res) => {
      addToast(res.message || "User suspended", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to suspend user", "error");
    },
  });

  const reactivateMutation = useMutation({
    mutationFn: ({ userId, reason }) => reactivateAdminUser(userId, reason),
    onSuccess: (res) => {
      addToast(res.message || "User reactivated", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to reactivate user", "error");
    },
  });

  const roleMutation = useMutation({
    mutationFn: ({ userId, role, reason }) => updateAdminUserRole(userId, role, reason),
    onSuccess: (res) => {
      addToast(res.message || "Role updated", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      closeModal();
    },
    onError: (err) => {
      addToast(err?.response?.data?.detail || "Failed to update role", "error");
    },
  });

  const closeModal = () => {
    setSelectedUser(null);
    setActionType(null);
    setReason("");
  };

  const handleActionSubmit = (e) => {
    e.preventDefault();
    if (!reason.trim() && actionType !== "detail") {
      addToast("A valid explanation reason is mandatory for audit logging.", "warning");
      return;
    }

    if (actionType === "suspend") {
      suspendMutation.mutate({ userId: selectedUser.id, reason });
    } else if (actionType === "reactivate") {
      reactivateMutation.mutate({ userId: selectedUser.id, reason });
    } else if (actionType === "role") {
      roleMutation.mutate({ userId: selectedUser.id, role: targetRole, reason });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">User Management</h1>
          <p className="text-sm text-slate-400">
            Inspect platform accounts, contextual capabilities, and manage suspensions with audit safety.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          {/* Role Filter */}
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Roles</option>
            <option value="USER">USER</option>
            <option value="ADMIN">ADMIN</option>
          </select>

          {/* Status Filter */}
          <select
            value={activeFilter}
            onChange={(e) => {
              setActiveFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="true">Active Only</option>
            <option value="false">Suspended Only</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3.5 px-4">User</th>
                <th className="py-3.5 px-4">Platform Role</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Capabilities</th>
                <th className="py-3.5 px-4">Sessions</th>
                <th className="py-3.5 px-4">Wallet</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    Loading platform users...
                  </td>
                </tr>
              ) : data?.items?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    No users matching the filter criteria.
                  </td>
                </tr>
              ) : (
                data?.items?.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <img
                          src={user.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${user.id}`}
                          alt={user.name}
                          className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 object-cover"
                        />
                        <div>
                          <div className="font-semibold text-slate-100">{user.name}</div>
                          <div className="text-xs text-slate-400 font-mono">{user.email}</div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          user.role === "ADMIN"
                            ? "bg-purple-500/10 border border-purple-500/30 text-purple-300"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {user.role === "ADMIN" && <Shield className="w-3 h-3 text-purple-400" />}
                        {user.role}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                          user.is_active
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {user.is_active ? "Active" : "Suspended"}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="text-xs space-y-0.5">
                        <div className="text-slate-300">
                          Teach: <span className="text-indigo-400 font-semibold">{user.teaching_skills.length} skills</span>
                        </div>
                        <div className="text-slate-400">
                          Learn: <span>{user.learning_skills.length} skills</span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-xs font-mono text-slate-300">
                      {user.sessions?.total || 0}
                    </td>

                    <td className="py-3.5 px-4 text-xs font-semibold text-amber-400 font-mono">
                      {user.wallet_balance} 🪙
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => {
                            setSelectedUser(user);
                            setActionType("detail");
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => {
                            setSelectedUser(user);
                            setTargetRole(user.role === "ADMIN" ? "USER" : "ADMIN");
                            setActionType("role");
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition-colors"
                          title="Change Role"
                        >
                          <Shield className="w-4 h-4" />
                        </button>

                        {user.is_active ? (
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setActionType("suspend");
                            }}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                            title="Suspend User"
                          >
                            <UserX className="w-4 h-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setActionType("reactivate");
                            }}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                            title="Reactivate User"
                          >
                            <UserCheck className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <strong className="text-slate-200">{data?.page || 1}</strong> of{" "}
            <strong className="text-slate-200">{data?.total_pages || 1}</strong> ({data?.total || 0} users)
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

      {/* Confirmation & Action Dialog */}
      {selectedUser && actionType && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="max-w-md w-full rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100">
                {actionType === "suspend" && "Suspend User Account"}
                {actionType === "reactivate" && "Reactivate User Account"}
                {actionType === "role" && "Modify Platform Role"}
                {actionType === "detail" && "User Profile Details"}
              </h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            {actionType === "detail" ? (
              <div className="space-y-4 text-xs">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-slate-400">Name: <strong className="text-slate-200">{selectedUser.name}</strong></div>
                  <div className="text-slate-400">Email: <strong className="text-slate-200">{selectedUser.email}</strong></div>
                  <div className="text-slate-400">Role: <strong className="text-slate-200">{selectedUser.role}</strong></div>
                  <div className="text-slate-400">Department: <strong className="text-slate-200">{selectedUser.department || "N/A"}</strong></div>
                  <div className="text-slate-400">Year: <strong className="text-slate-200">{selectedUser.year || "N/A"}</strong></div>
                </div>

                <div className="space-y-2">
                  <div className="font-semibold text-slate-300">Teaching Skills:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedUser.teaching_skills?.length > 0 ? (
                      selectedUser.teaching_skills.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                          {s.name} ({s.status})
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500">None claimed</span>
                    )}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={closeModal}
                    className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleActionSubmit} className="space-y-4">
                <p className="text-xs text-slate-400">
                  Target Account: <strong className="text-slate-200">{selectedUser.email}</strong>
                </p>

                {actionType === "role" && (
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Target Role</label>
                    <select
                      value={targetRole}
                      onChange={(e) => setTargetRole(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200"
                    >
                      <option value="USER">USER</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Mandatory Reason for Audit Trail
                  </label>
                  <textarea
                    rows="3"
                    required
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Provide justification for this administrative action..."
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className={`flex-1 py-2 rounded-xl text-xs font-semibold text-white transition-colors ${
                      actionType === "suspend"
                        ? "bg-red-600 hover:bg-red-500"
                        : "bg-indigo-600 hover:bg-indigo-500"
                    }`}
                  >
                    Confirm Action
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
