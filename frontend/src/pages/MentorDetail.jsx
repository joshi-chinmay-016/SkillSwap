import React, { useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "motion/react";
import api from "../services/api";
import { getMentorAvailabilityWindows, getMentorBookableSlots } from "../api/availabilityApi";
import Avatar from "../components/common/Avatar";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import Modal from "../components/common/Modal";
import Input from "../components/common/Input";
import PageTransition from "../components/common/PageTransition";
import CredibilityBadge from "../components/verification/CredibilityBadge";
import {
  ArrowLeft,
  Star,
  Calendar,
  BookOpen,
  Award,
  Clock,
  Video,
  AlertCircle,
  CheckCircle,
  ShieldCheck,
  Zap,
  Sparkles,
  UserCheck,
  CalendarDays,
  CheckCircle2,
  Info,
} from "lucide-react";

export default function MentorDetail() {
  const { id } = useParams();
  const mentorId = parseInt(id);
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const initialName = location.state?.mentorName || "Mentor Profile";
  const initialRating = location.state?.averageRating || 0;

  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [selectedDate, setSelectedDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().slice(0, 10);
  });
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [bookingError, setBookingError] = useState("");

  // 1. Fetch Mentor Profile
  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ["mentorProfile", mentorId],
    queryFn: async () => {
      const res = await api.get(`/profiles/${mentorId}`);
      return res.data;
    },
  });

  // 2. Fetch Mentor Skills
  const { data: mentorSkills = [], isLoading: isSkillsLoading } = useQuery({
    queryKey: ["mentorSkills", mentorId],
    queryFn: async () => {
      const res = await api.get(`/skills/user/${mentorId}`);
      return res.data;
    },
  });

  // 3. Fetch Real Mentor Availability Windows
  const { data: availabilityWindows = [], isLoading: isAvailLoading } = useQuery({
    queryKey: ["mentorAvailabilityWindows", mentorId],
    queryFn: () => getMentorAvailabilityWindows(mentorId),
  });

  // 4. Fetch Real Bookable Slots for selected date
  const {
    data: slotsResponse,
    isLoading: isSlotsLoading,
    refetch: refetchSlots,
  } = useQuery({
    queryKey: ["mentorBookableSlots", mentorId, selectedDate],
    queryFn: () => getMentorBookableSlots(mentorId, selectedDate),
    enabled: isBookModalOpen && !!selectedDate,
  });

  const teachSkills = mentorSkills.filter((s) => s.type === "teach");
  const learnSkills = mentorSkills.filter((s) => s.type === "learn");

  // Booking Mutation
  const bookSessionMutation = useMutation({
    mutationFn: async ({ payload, idempotencyKey }) => {
      const headers = idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {};
      const res = await api.post("/sessions", payload, { headers });
      return res.data;
    },
    onSuccess: () => {
      setBookingSuccess(true);
      queryClient.invalidateQueries({ queryKey: ["upcomingSessions"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["mentorBookableSlots", mentorId, selectedDate] });
      setTimeout(() => {
        setIsBookModalOpen(false);
        setBookingSuccess(false);
        navigate("/sessions");
      }, 1800);
    },
    onError: (err) => {
      const status = err.response?.status;
      const msg = err.response?.data?.detail;

      if (status === 409) {
        setBookingError("⚠️ This slot was just booked by another learner. Please select another time.");
        refetchSlots();
      } else if (status === 429) {
        setBookingError("⚠️ Too many requests. Please try again shortly.");
      } else {
        setBookingError(msg || "We couldn't complete the booking. Your booking was not confirmed.");
      }
    },
  });

  const handleOpenBooking = () => {
    setBookingError("");
    setBookingSuccess(false);
    setSelectedSlot(null);

    if (teachSkills.length > 0) {
      setSelectedSkillId(teachSkills[0].skill_id?.toString() || "");
    }

    // Default to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setSelectedDate(tomorrow.toISOString().slice(0, 10));

    setIsBookModalOpen(true);
  };

  const handleBookSubmit = (e) => {
    e.preventDefault();
    setBookingError("");

    if (!selectedSkillId) {
      setBookingError("Please select a skill to learn.");
      return;
    }
    if (!selectedSlot) {
      setBookingError("Please select an available time slot.");
      return;
    }

    const idempotencyKey = `book-${mentorId}-${selectedSlot.slot_start}-${Date.now()}`;

    bookSessionMutation.mutate({
      payload: {
        mentor_id: mentorId,
        skill_id: parseInt(selectedSkillId),
        scheduled_at: selectedSlot.slot_start,
        duration_minutes: selectedSlot.duration_minutes || 60,
      },
      idempotencyKey,
    });
  };

  const isLoading = isProfileLoading || isSkillsLoading || isAvailLoading;
  const availableSlots = slotsResponse?.slots || [];
  const minDateString = new Date().toISOString().slice(0, 10);

  return (
    <PageTransition className="space-y-6 text-left">
      {/* Back Button */}
      <div>
        <button
          type="button"
          onClick={() => navigate("/mentors")}
          className="inline-flex items-center gap-2 text-xs font-bold text-text-secondary hover:text-accent cursor-pointer transition-colors"
        >
          <ArrowLeft size={16} />
          <span>Back to Mentors</span>
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <div className="h-40 w-full bg-border/40 animate-pulse rounded-3xl" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 h-64 bg-border/40 animate-pulse rounded-3xl" />
            <div className="h-64 bg-border/40 animate-pulse rounded-3xl" />
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Header Card */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card-bg border border-card-border p-6 sm:p-8 rounded-3xl flex flex-col sm:flex-row items-center sm:items-start justify-between gap-6 shadow-md relative overflow-hidden"
          >
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 text-center sm:text-left">
              <Avatar
                src={profile?.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${initialName}`}
                alt={initialName}
                size="2xl"
                className="ring-4 ring-accent/20 shrink-0"
              />
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
                  <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text">
                    {initialName}
                  </h1>
                  {teachSkills[0] && (
                    <CredibilityBadge
                      status={teachSkills[0].verification_status || "CLAIMED"}
                      score={teachSkills[0].score}
                      size="md"
                    />
                  )}
                </div>
                <p className="text-xs sm:text-sm font-semibold text-text-secondary">
                  {profile?.department ? `${profile.department} Student` : "Peer Mentor"} • Year {profile?.year || 1}
                </p>

                <div className="flex items-center justify-center sm:justify-start gap-1 text-xs pt-1">
                  <Star size={16} className="text-amber-500 fill-amber-500" />
                  <span className="font-extrabold text-sm text-text">
                    {initialRating > 0 ? Number(initialRating).toFixed(1) : "New Mentor"}
                  </span>
                </div>
              </div>
            </div>

            <div className="shrink-0 mt-2 sm:mt-0">
              <Button
                onClick={handleOpenBooking}
                variant="primary"
                size="md"
                className="font-bold shadow-glow"
                leftIcon={Calendar}
              >
                Book Swap Session
              </Button>
            </div>
          </motion.div>

          {/* Grid Details */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Bio Card & Availability Card */}
            <div className="lg:col-span-2 space-y-6">
              <Card title="About Mentor" subtitle="Background & Teaching Philosophy">
                {profile?.bio ? (
                  <p className="text-sm text-text-secondary whitespace-pre-line leading-relaxed">
                    {profile.bio}
                  </p>
                ) : (
                  <p className="text-sm text-text-secondary italic">
                    This mentor has not provided a biography yet.
                  </p>
                )}
              </Card>

              {/* Real Availability Schedule Card */}
              <Card title="Weekly Availability Windows" subtitle="Authoritative hours set by mentor">
                {availabilityWindows.length === 0 ? (
                  <div className="p-4 rounded-2xl bg-bg-alt border border-border text-center space-y-1">
                    <CalendarDays size={24} className="mx-auto text-text-muted opacity-60" />
                    <p className="text-xs font-semibold text-text">No active schedule configured</p>
                    <p className="text-[11px] text-text-secondary">
                      This mentor has not published weekly availability slots yet.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {availabilityWindows.map((slot) => (
                      <div
                        key={slot.id}
                        className="p-3.5 rounded-2xl bg-bg-alt/80 border border-border/80 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-xl bg-accent/10 text-accent flex items-center justify-center font-bold text-xs">
                            {slot.day_of_week.slice(0, 3)}
                          </div>
                          <div>
                            <p className="text-xs font-bold text-text">{slot.day_of_week}</p>
                            <p className="text-[11px] text-text-secondary font-medium flex items-center gap-1">
                              <Clock size={11} className="text-accent" />
                              <span>
                                {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)} ({slot.timezone || "UTC"})
                              </span>
                            </p>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                          Active
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            {/* Skills Card */}
            <div className="space-y-6">
              <Card title="Mentor's Skill Profile" subtitle="Active competencies">
                <div className="space-y-5">
                  {/* Skills to Teach */}
                  <div>
                    <h4 className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                      <Award size={14} /> Teaches & Offers
                    </h4>
                    {teachSkills.length === 0 ? (
                      <p className="text-xs text-text-secondary italic">No teaching skills listed</p>
                    ) : (
                      <div className="space-y-2">
                        {teachSkills.map((s) => (
                          <div
                            key={s.id}
                            className="flex items-center justify-between p-2.5 bg-emerald-500/5 rounded-xl border border-emerald-500/15"
                          >
                            <span className="text-xs font-bold text-text">
                              {s.skill?.name || s.name}
                            </span>
                            <CredibilityBadge
                              status={s.verification_status || "CLAIMED"}
                              score={s.score}
                              size="sm"
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Skills to Learn */}
                  <div>
                    <h4 className="text-xs font-bold text-accent uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                      <BookOpen size={14} /> Wants to Learn
                    </h4>
                    {learnSkills.length === 0 ? (
                      <p className="text-xs text-text-secondary italic">No learning goals listed</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {learnSkills.map((s) => (
                          <span
                            key={s.id}
                            className="px-3 py-1 text-xs font-semibold bg-accent/10 text-accent rounded-full border border-accent/20"
                          >
                            {s.skill?.name || s.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* Authoritative Booking Form Modal */}
      <Modal
        isOpen={isBookModalOpen}
        onClose={() => !bookSessionMutation.isPending && setIsBookModalOpen(false)}
        title={`Book Peer Session with ${initialName}`}
        size="md"
        closeOnOverlayClick={!bookSessionMutation.isPending}
      >
        {bookingSuccess ? (
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="py-8 flex flex-col items-center gap-3 text-center"
          >
            <div className="w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center border border-emerald-500/20 shadow-glow">
              <CheckCircle size={36} />
            </div>
            <h3 className="font-extrabold text-lg text-text">Session Booked Successfully!</h3>
            <p className="text-xs text-text-secondary max-w-xs">
              Your 1-on-1 swap session is confirmed in the database. Redirecting to your sessions...
            </p>
          </motion.div>
        ) : (
          <form onSubmit={handleBookSubmit} className="space-y-4">
            {bookingError && (
              <div className="p-3 text-xs bg-danger/10 border border-danger/20 text-danger rounded-xl font-medium flex items-center gap-2">
                <AlertCircle size={15} className="shrink-0" />
                <span>{bookingError}</span>
              </div>
            )}

            {/* Select Skill */}
            <div className="space-y-1.5 text-left">
              <label htmlFor="select-skill" className="text-xs font-bold text-text-secondary">
                Select Skill to Learn
              </label>
              <select
                id="select-skill"
                value={selectedSkillId}
                onChange={(e) => setSelectedSkillId(e.target.value)}
                disabled={bookSessionMutation.isPending}
                className="w-full px-3.5 py-2.5 text-xs font-semibold rounded-xl border border-border bg-bg text-text shadow-xs focus:outline-none focus:border-accent"
              >
                {teachSkills.length === 0 ? (
                  <option value="">No teaching skills available</option>
                ) : (
                  teachSkills.map((s) => (
                    <option key={s.skill_id} value={s.skill_id}>
                      {s.skill?.name || s.name}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Select Target Date */}
            <div className="space-y-1.5 text-left">
              <label htmlFor="select-date" className="text-xs font-bold text-text-secondary">
                Session Date
              </label>
              <Input
                id="select-date"
                type="date"
                min={minDateString}
                value={selectedDate}
                onChange={(e) => {
                  setSelectedDate(e.target.value);
                  setSelectedSlot(null);
                }}
                disabled={bookSessionMutation.isPending}
              />
            </div>

            {/* Real Bookable Discrete Slots */}
            <div className="space-y-1.5 text-left">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-text-secondary">
                  Available 60-Min Time Slots
                </label>
                {isSlotsLoading && (
                  <span className="text-[10px] text-accent animate-pulse font-semibold">
                    Checking database availability...
                  </span>
                )}
              </div>

              {isSlotsLoading ? (
                <div className="grid grid-cols-2 gap-2">
                  <div className="h-10 bg-border/40 animate-pulse rounded-xl" />
                  <div className="h-10 bg-border/40 animate-pulse rounded-xl" />
                </div>
              ) : availableSlots.length === 0 ? (
                <div className="p-3.5 bg-bg-alt border border-border rounded-xl text-center space-y-1">
                  <p className="text-xs font-bold text-text">No slots available on this date</p>
                  <p className="text-[11px] text-text-secondary">
                    The mentor does not have active availability on {slotsResponse?.day_of_week || "this day"}.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1">
                  {availableSlots.map((slot, index) => {
                    const isSelected = selectedSlot?.slot_start === slot.slot_start;
                    return (
                      <button
                        key={index}
                        type="button"
                        disabled={!slot.is_available || bookSessionMutation.isPending}
                        onClick={() => setSelectedSlot(slot)}
                        className={`p-2.5 text-xs font-bold rounded-xl border text-left transition-all cursor-pointer ${
                          !slot.is_available
                            ? "bg-bg-alt/50 border-border/50 text-text-muted opacity-50 cursor-not-allowed line-through"
                            : isSelected
                            ? "bg-accent text-white border-accent shadow-glow"
                            : "bg-surface-elevated hover:bg-bg-alt border-border text-text"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span>{slot.formatted_time}</span>
                          {isSelected && <CheckCircle2 size={13} className="shrink-0" />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Meeting Link Preview */}
            <div className="p-3.5 bg-bg-alt border border-border rounded-xl flex items-center justify-between text-xs text-text-secondary mt-1">
              <div className="flex items-center gap-2">
                <Video size={15} className="text-accent" />
                <span className="font-medium">Video Room (Auto-Generated)</span>
              </div>
              <span className="font-bold text-emerald-500">Ready</span>
            </div>

            {/* Coin deduction info */}
            <p className="text-[11px] text-text-secondary mt-1 text-left italic">
              Note: Scheduling a peer lesson will atomically deduct 5 Skill Coins from your wallet balance.
            </p>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsBookModalOpen(false)}
                disabled={bookSessionMutation.isPending}
                className="text-xs font-semibold"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                isLoading={bookSessionMutation.isPending}
                disabled={teachSkills.length === 0 || !selectedSlot}
                className="font-bold text-xs shadow-glow"
              >
                Confirm & Book Swap
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </PageTransition>
  );
}

