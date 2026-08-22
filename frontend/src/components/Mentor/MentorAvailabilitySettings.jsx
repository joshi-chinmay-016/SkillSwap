import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "motion/react";
import {
  getMyAvailability,
  createAvailability,
  createAllTimeAvailability,
  deleteAvailability,
} from "../../api/availabilityApi";
import Button from "../common/Button";
import Input from "../common/Input";
import Card from "../common/Card";
import {
  Calendar,
  Clock,
  Plus,
  Trash2,
  AlertCircle,
  CheckCircle,
  CalendarDays,
  Sparkles,
  Repeat,
  CalendarCheck2,
  Globe,
  Zap,
} from "lucide-react";

const DAYS_OF_WEEK = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export default function MentorAvailabilitySettings() {
  const queryClient = useQueryClient();
  const [scheduleType, setScheduleType] = useState("all_time"); // "all_time" | "date" | "recurring"
  const [specificDate, setSpecificDate] = useState(
    new Date(Date.now() + 86400000).toISOString().slice(0, 10)
  );
  const [dayOfWeek, setDayOfWeek] = useState("Monday");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("18:00");
  const [timezone, setTimezone] = useState("UTC");
  const [filterType, setFilterType] = useState("all"); // "all" | "date" | "recurring"
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Fetch my availability
  const { data: mySlots = [], isLoading } = useQuery({
    queryKey: ["myAvailabilitySlots"],
    queryFn: getMyAvailability,
  });

  // Create Slot Mutation
  const createMutation = useMutation({
    mutationFn: (payload) => createAvailability(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["myAvailabilitySlots"] });
      setSuccessMsg("Availability window added successfully!");
      setErrorMsg("");
      setTimeout(() => setSuccessMsg(""), 3500);
    },
    onError: (err) => {
      setErrorMsg(err.response?.data?.detail || "Failed to add availability window.");
      setSuccessMsg("");
    },
  });

  // All-Time Mutation
  const allTimeMutation = useMutation({
    mutationFn: (payload) => createAllTimeAvailability(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["myAvailabilitySlots"] });
      setSuccessMsg("All-time (Monday–Sunday) availability configured!");
      setErrorMsg("");
      setTimeout(() => setSuccessMsg(""), 3500);
    },
    onError: (err) => {
      setErrorMsg(err.response?.data?.detail || "Failed to set all-time availability.");
    },
  });

  // Delete Slot Mutation
  const deleteMutation = useMutation({
    mutationFn: (slotId) => deleteAvailability(slotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["myAvailabilitySlots"] });
      setSuccessMsg("Availability window removed.");
      setTimeout(() => setSuccessMsg(""), 3000);
    },
    onError: (err) => {
      setErrorMsg(err.response?.data?.detail || "Failed to delete slot.");
    },
  });

  const handleAddSlot = (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (startTime >= endTime) {
      setErrorMsg("Start time must be earlier than end time.");
      return;
    }

    if (scheduleType === "all_time") {
      allTimeMutation.mutate({
        start_time: startTime + ":00",
        end_time: endTime + ":00",
        timezone: timezone,
        is_active: true,
      });
      return;
    }

    const payload = {
      start_time: startTime + ":00",
      end_time: endTime + ":00",
      timezone: timezone,
      is_active: true,
    };

    if (scheduleType === "date") {
      if (!specificDate) {
        setErrorMsg("Please select a specific calendar date.");
        return;
      }
      payload.specific_date = specificDate;
      const dateObj = new Date(specificDate + "T00:00:00");
      payload.day_of_week = dateObj.toLocaleDateString("en-US", { weekday: "long" });
    } else {
      payload.day_of_week = dayOfWeek;
      payload.specific_date = null;
    }

    createMutation.mutate(payload);
  };

  const applyPreset = (presetStart, presetEnd, isAllTime = true) => {
    setErrorMsg("");
    setSuccessMsg("");
    setStartTime(presetStart);
    setEndTime(presetEnd);

    if (isAllTime) {
      allTimeMutation.mutate({
        start_time: presetStart + ":00",
        end_time: presetEnd + ":00",
        timezone: timezone,
        is_active: true,
      });
    }
  };

  const getComputedWeekdayFromDate = (dateStr) => {
    if (!dateStr) return "";
    try {
      const d = new Date(dateStr + "T00:00:00");
      return d.toLocaleDateString("en-US", {
        weekday: "long",
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const filteredSlots = mySlots.filter((slot) => {
    if (filterType === "date") return Boolean(slot.specific_date);
    if (filterType === "recurring") return !slot.specific_date;
    return true;
  });

  const todayStr = new Date().toISOString().slice(0, 10);

  return (
    <div className="space-y-6 text-left">
      <Card
        title="Mentor Availability Schedule"
        subtitle="Configure all-time free hours, specific calendar dates, or recurring weekly windows for 1-on-1 peer lessons."
      >
        <div className="space-y-6">
          {/* Status Messages */}
          {errorMsg && (
            <div className="p-3 text-xs bg-danger/10 border border-danger/20 text-danger rounded-xl font-medium flex items-center gap-2">
              <AlertCircle size={15} className="shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-xl font-medium flex items-center gap-2">
              <CheckCircle size={15} className="shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Quick Presets Bar */}
          <div className="p-3.5 bg-gradient-to-r from-accent/10 via-purple-500/10 to-emerald-500/10 border border-accent/20 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-accent text-white shadow-xs">
                <Zap size={15} />
              </div>
              <div>
                <p className="text-xs font-black text-text">Quick Availability Presets</p>
                <p className="text-[10px] text-text-secondary">
                  Set all-time availability with a single click
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => applyPreset("00:00", "23:59", true)}
                className="px-3 py-1.5 rounded-xl bg-bg border border-border hover:border-accent text-[11px] font-bold text-text hover:text-accent transition-all cursor-pointer shadow-xs"
              >
                🌐 24/7 Always Open
              </button>
              <button
                type="button"
                onClick={() => applyPreset("09:00", "18:00", true)}
                className="px-3 py-1.5 rounded-xl bg-bg border border-border hover:border-accent text-[11px] font-bold text-text hover:text-accent transition-all cursor-pointer shadow-xs"
              >
                💼 Everyday 9am - 6pm
              </button>
              <button
                type="button"
                onClick={() => applyPreset("18:00", "22:00", true)}
                className="px-3 py-1.5 rounded-xl bg-bg border border-border hover:border-accent text-[11px] font-bold text-text hover:text-accent transition-all cursor-pointer shadow-xs"
              >
                🌙 Evenings 6pm - 10pm
              </button>
            </div>
          </div>

          {/* Add Window Form */}
          <form onSubmit={handleAddSlot} className="p-5 rounded-2xl bg-bg-alt/70 border border-border space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/80">
              <h4 className="text-xs font-bold uppercase tracking-wider text-text flex items-center gap-1.5">
                <Plus size={14} className="text-accent" /> Add Availability Window
              </h4>

              {/* Schedule Type Toggle */}
              <div className="inline-flex p-1 rounded-xl bg-bg border border-border text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setScheduleType("all_time")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                    scheduleType === "all_time"
                      ? "bg-accent text-white shadow-xs"
                      : "text-text-secondary hover:text-text"
                  }`}
                >
                  <Globe size={13} />
                  <span>All-Time (Mon-Sun)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setScheduleType("date")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                    scheduleType === "date"
                      ? "bg-accent text-white shadow-xs"
                      : "text-text-secondary hover:text-text"
                  }`}
                >
                  <Calendar size={13} />
                  <span>Specific Date</span>
                </button>
                <button
                  type="button"
                  onClick={() => setScheduleType("recurring")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                    scheduleType === "recurring"
                      ? "bg-accent text-white shadow-xs"
                      : "text-text-secondary hover:text-text"
                  }`}
                >
                  <Repeat size={13} />
                  <span>Single Weekday</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3.5 pt-1">
              {/* Date or Day Selector */}
              {scheduleType === "all_time" ? (
                <div className="space-y-1 sm:col-span-1">
                  <label className="text-[11px] font-bold text-text-secondary">Coverage</label>
                  <div className="h-[38px] px-3 rounded-xl border border-border bg-bg text-text flex items-center font-bold text-xs">
                    All 7 Days (Everyday)
                  </div>
                  <p className="text-[10px] text-accent font-bold mt-1">
                    Applies to Mon, Tue, Wed, Thu, Fri, Sat, Sun
                  </p>
                </div>
              ) : scheduleType === "date" ? (
                <div className="space-y-1 sm:col-span-1">
                  <label className="text-[11px] font-bold text-text-secondary">Calendar Date</label>
                  <Input
                    type="date"
                    min={todayStr}
                    value={specificDate}
                    onChange={(e) => setSpecificDate(e.target.value)}
                    className="h-[38px] text-xs font-semibold"
                    required
                  />
                  {specificDate && (
                    <p className="text-[10px] text-accent font-bold mt-1 truncate">
                      {getComputedWeekdayFromDate(specificDate)}
                    </p>
                  )}
                </div>
              ) : (
                <div className="space-y-1 sm:col-span-1">
                  <label className="text-[11px] font-bold text-text-secondary">Day of Week</label>
                  <select
                    value={dayOfWeek}
                    onChange={(e) => setDayOfWeek(e.target.value)}
                    className="w-full h-[38px] px-3 text-xs font-semibold rounded-xl border border-border bg-bg text-text focus:outline-none focus:border-accent"
                  >
                    {DAYS_OF_WEEK.map((d) => (
                      <option key={d} value={d}>
                        Every {d}
                      </option>
                    ))}
                  </select>
                  <p className="text-[10px] text-text-secondary font-medium mt-1">Repeats weekly</p>
                </div>
              )}

              {/* Start Time */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-text-secondary">Start Time</label>
                <Input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="h-[38px] text-xs"
                  required
                />
              </div>

              {/* End Time */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-text-secondary">End Time</label>
                <Input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="h-[38px] text-xs"
                  required
                />
              </div>

              {/* Submit Button */}
              <div className="flex items-end">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={createMutation.isPending || allTimeMutation.isPending}
                  className="w-full h-[38px] text-xs font-bold shadow-glow"
                  leftIcon={Plus}
                >
                  {scheduleType === "all_time" ? "Set All-Time" : "Save Window"}
                </Button>
              </div>
            </div>
          </form>

          {/* Current Slots List */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h4 className="text-xs font-bold text-text flex items-center gap-1.5">
                <span>Active Availability ({mySlots.length} Total Windows)</span>
              </h4>

              {/* Filter Pills */}
              <div className="inline-flex p-1 rounded-xl bg-bg-alt border border-border text-[11px] font-bold">
                <button
                  type="button"
                  onClick={() => setFilterType("all")}
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                    filterType === "all" ? "bg-accent text-white" : "text-text-secondary hover:text-text"
                  }`}
                >
                  All ({mySlots.length})
                </button>
                <button
                  type="button"
                  onClick={() => setFilterType("date")}
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                    filterType === "date" ? "bg-accent text-white" : "text-text-secondary hover:text-text"
                  }`}
                >
                  Specific Dates ({mySlots.filter((s) => s.specific_date).length})
                </button>
                <button
                  type="button"
                  onClick={() => setFilterType("recurring")}
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                    filterType === "recurring" ? "bg-accent text-white" : "text-text-secondary hover:text-text"
                  }`}
                >
                  Weekly Recurring ({mySlots.filter((s) => !s.specific_date).length})
                </button>
              </div>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="h-20 bg-border/40 animate-pulse rounded-2xl" />
                <div className="h-20 bg-border/40 animate-pulse rounded-2xl" />
              </div>
            ) : filteredSlots.length === 0 ? (
              <div className="p-8 text-center bg-bg-alt/40 border border-border/80 rounded-2xl space-y-1.5">
                <CalendarDays size={28} className="mx-auto text-text-muted opacity-40" />
                <p className="text-xs font-bold text-text">No availability windows found</p>
                <p className="text-[11px] text-text-secondary max-w-sm mx-auto">
                  {filterType === "all"
                    ? "Set your all-time free hours, specific dates, or weekly hours above."
                    : `No ${filterType === "date" ? "specific date" : "weekly recurring"} windows configured.`}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {filteredSlots.map((slot) => {
                  const isDateSpecific = Boolean(slot.specific_date);
                  return (
                    <motion.div
                      key={slot.id}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-3.5 rounded-2xl bg-card-bg border border-border hover:border-accent/40 flex items-center justify-between shadow-xs transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-10 h-10 rounded-xl flex items-center justify-center font-extrabold text-xs shrink-0 ${
                            isDateSpecific
                              ? "bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20"
                              : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                          }`}
                        >
                          {isDateSpecific ? (
                            <CalendarCheck2 size={18} />
                          ) : (
                            <Repeat size={18} />
                          )}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <p className="text-xs font-extrabold text-text">
                              {isDateSpecific
                                ? `${slot.specific_date} (${slot.day_of_week})`
                                : `Every ${slot.day_of_week}`}
                            </p>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide ${
                                isDateSpecific
                                  ? "bg-purple-500/15 text-purple-600 dark:text-purple-400"
                                  : "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                              }`}
                            >
                              {isDateSpecific ? "Date" : "Weekly"}
                            </span>
                          </div>
                          <p className="text-[11px] text-text-secondary font-medium flex items-center gap-1 mt-0.5">
                            <Clock size={12} className="text-accent shrink-0" />
                            <span>
                              {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)} ({slot.timezone || "UTC"})
                            </span>
                          </p>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => deleteMutation.mutate(slot.id)}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-danger hover:bg-danger/10 rounded-xl transition-colors cursor-pointer shrink-0 ml-2"
                        title="Delete availability window"
                      >
                        <Trash2 size={15} />
                      </button>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
