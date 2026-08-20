import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "motion/react";
import { getMyAvailability, createAvailability, deleteAvailability } from "../../api/availabilityApi";
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
  const [dayOfWeek, setDayOfWeek] = useState("Monday");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [timezone, setTimezone] = useState("UTC");
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Fetch my availability
  const { data: mySlots = [], isLoading, isError } = useQuery({
    queryKey: ["myAvailabilitySlots"],
    queryFn: getMyAvailability,
  });

  // Create Slot Mutation
  const createMutation = useMutation({
    mutationFn: (payload) => createAvailability(payload),
    onSuccess: () => {
      queryClient.invalidateQueries(["myAvailabilitySlots"]);
      setSuccessMsg("Availability window added successfully!");
      setErrorMsg("");
      setTimeout(() => setSuccessMsg(""), 3000);
    },
    onError: (err) => {
      setErrorMsg(err.response?.data?.detail || "Failed to add availability window.");
      setSuccessMsg("");
    },
  });

  // Delete Slot Mutation
  const deleteMutation = useMutation({
    mutationFn: (slotId) => deleteAvailability(slotId),
    onSuccess: () => {
      queryClient.invalidateQueries(["myAvailabilitySlots"]);
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

    createMutation.mutate({
      day_of_week: dayOfWeek,
      start_time: startTime + ":00",
      end_time: endTime + ":00",
      timezone: timezone,
      is_active: true,
    });
  };

  return (
    <div className="space-y-6">
      <Card
        title="Mentor Availability Schedule"
        subtitle="Configure weekly windows when learners can book 1-on-1 skill swap sessions with you."
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

          {/* Add Window Form */}
          <form onSubmit={handleAddSlot} className="p-4 rounded-2xl bg-bg-alt/60 border border-border space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-text flex items-center gap-1.5">
              <Plus size={14} className="text-accent" /> Add Availability Window
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              {/* Day */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-text-secondary">Day of Week</label>
                <select
                  value={dayOfWeek}
                  onChange={(e) => setDayOfWeek(e.target.value)}
                  className="w-full h-[38px] px-3 text-xs font-semibold rounded-xl border border-border bg-bg text-text focus:outline-none focus:border-accent"
                >
                  {DAYS_OF_WEEK.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              {/* Start Time */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-text-secondary">Start Time</label>
                <Input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="h-[38px] text-xs"
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
                />
              </div>

              {/* Submit Button */}
              <div className="flex items-end">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={createMutation.isPending}
                  className="w-full h-[38px] text-xs font-bold shadow-xs"
                  leftIcon={Plus}
                >
                  Add Window
                </Button>
              </div>
            </div>
          </form>

          {/* Current Slots List */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-text flex items-center justify-between">
              <span>Active Weekly Schedule ({mySlots.length} Windows)</span>
            </h4>

            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="h-16 bg-border/40 animate-pulse rounded-2xl" />
                <div className="h-16 bg-border/40 animate-pulse rounded-2xl" />
              </div>
            ) : mySlots.length === 0 ? (
              <div className="p-8 text-center bg-bg-alt/40 border border-border/80 rounded-2xl space-y-1.5">
                <CalendarDays size={28} className="mx-auto text-text-muted opacity-40" />
                <p className="text-xs font-bold text-text">No availability windows configured yet</p>
                <p className="text-[11px] text-text-secondary max-w-sm mx-auto">
                  Add days and hours when you are free to teach. Learners will only be able to book sessions inside these exact windows.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {mySlots.map((slot) => (
                  <motion.div
                    key={slot.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3.5 rounded-2xl bg-card-bg border border-border flex items-center justify-between shadow-xs"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-accent/10 text-accent flex items-center justify-center font-extrabold text-xs">
                        {slot.day_of_week.slice(0, 3)}
                      </div>
                      <div>
                        <p className="text-xs font-bold text-text">{slot.day_of_week}</p>
                        <p className="text-[11px] text-text-secondary font-medium flex items-center gap-1">
                          <Clock size={12} className="text-accent" />
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
                      className="p-2 text-danger hover:bg-danger/10 rounded-xl transition-colors cursor-pointer"
                      title="Delete availability window"
                    >
                      <Trash2 size={15} />
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
