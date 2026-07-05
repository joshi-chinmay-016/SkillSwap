import React, { useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../services/api";
import Avatar from "../components/common/Avatar";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import Modal from "../components/common/Modal";
import Input from "../components/common/Input";
import {
  ArrowLeft,
  Star,
  Calendar,
  BookOpen,
  Award,
  Clock,
  Video,
  AlertCircle,
  CheckCircle
} from "lucide-react";

export default function MentorDetail() {
  const { id } = useParams();
  const mentorId = parseInt(id);
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Retrieve initial information from state if available for faster layout load
  const initialName = location.state?.mentorName || "Mentor Profile";
  const initialRating = location.state?.averageRating || 0;

  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
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

  // Filters
  const teachSkills = mentorSkills.filter((s) => s.type === "teach");
  const learnSkills = mentorSkills.filter((s) => s.type === "learn");

  // Booking Mutation
  const bookSessionMutation = useMutation({
    mutationFn: async (payload) => {
      const res = await api.post("/sessions", payload);
      return res.data;
    },
    onSuccess: () => {
      setBookingSuccess(true);
      // Invalidate queries to refresh sessions lists
      queryClient.invalidateQueries(["upcomingSessions"]);
      setTimeout(() => {
        setIsBookModalOpen(false);
        setBookingSuccess(false);
        navigate("/sessions");
      }, 2000);
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || "Booking failed. You might not have enough coins.";
      setBookingError(msg);
    },
  });

  const handleOpenBooking = () => {
    setBookingError("");
    setBookingSuccess(false);
    // Auto-select first teaching skill if available
    if (teachSkills.length > 0) {
      setSelectedSkillId(teachSkills[0].skill_id.toString());
    }
    // Set default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    setScheduledAt(tomorrow.toISOString().slice(0, 16)); // format for datetime-local input
    
    setIsBookModalOpen(true);
  };

  const handleBookSubmit = (e) => {
    e.preventDefault();
    setBookingError("");

    if (!selectedSkillId) {
      setBookingError("Please select a skill to learn.");
      return;
    }
    if (!scheduledAt) {
      setBookingError("Please select a date and time.");
      return;
    }

    // Auto-generate Jitsi video meeting room link
    const roomName = `skillswap-${mentorId}-${Date.now().toString().slice(-6)}`;
    const meetingLink = `https://meet.jit.si/${roomName}`;

    bookSessionMutation.mutate({
      mentor_id: mentorId,
      skill_id: parseInt(selectedSkillId),
      scheduled_at: new Date(scheduledAt).toISOString(),
      meeting_link: meetingLink,
    });
  };

  const isLoading = isProfileLoading || isSkillsLoading;

  return (
    <div className="flex flex-col gap-6 text-left">
      {/* Back button */}
      <div>
        <button
          type="button"
          onClick={() => navigate("/mentors")}
          className="inline-flex items-center gap-2 text-xs font-semibold text-text-secondary hover:text-text cursor-pointer transition-colors"
        >
          <ArrowLeft size={16} /> Back to Mentors
        </button>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-6">
          <div className="h-28 w-full bg-border/40 animate-pulse rounded-lg" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 h-64 bg-border/40 animate-pulse rounded-lg" />
            <div className="h-48 bg-border/40 animate-pulse rounded-lg" />
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Header Card */}
          <div className="bg-bg border border-border p-6 rounded-xl flex flex-col sm:flex-row items-center sm:items-start gap-5 shadow-xs">
            <Avatar
              src={profile?.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${initialName}`}
              alt={initialName}
              size="2xl"
            />
            <div className="flex-1 text-center sm:text-left">
              <h2 className="text-2xl font-bold tracking-tight text-text m-0">
                {initialName}
              </h2>
              <p className="text-sm font-medium text-text-secondary mt-1">
                {profile?.department ? `${profile.department} Major` : "Student"} • Year {profile?.year || 1}
              </p>
              
              <div className="flex items-center justify-center sm:justify-start gap-1 mt-2 text-xs">
                <div className="flex items-center text-yellow-500">
                  <Star size={16} fill="currentColor" />
                </div>
                <span className="font-bold text-sm text-text">
                  {initialRating > 0 ? initialRating.toFixed(1) : "New Mentor"}
                </span>
              </div>
            </div>
            
            <div className="shrink-0 mt-2 sm:mt-0">
              <Button onClick={handleOpenBooking} variant="primary" size="md">
                <Calendar size={16} /> Book Swap Session
              </Button>
            </div>
          </div>

          {/* Grid details */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Bio Card */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              <Card title="About Mentor">
                {profile?.bio ? (
                  <p className="text-sm text-text-secondary whitespace-pre-line leading-relaxed">
                    {profile.bio}
                  </p>
                ) : (
                  <p className="text-sm text-text-secondary italic">
                    This mentor hasn't written a biography yet.
                  </p>
                )}
              </Card>
            </div>

            {/* Skills Card */}
            <div className="flex flex-col gap-6">
              <Card title="Mentor's Expertise">
                <div className="flex flex-col gap-4">
                  {/* Skills to Teach */}
                  <div>
                    <h4 className="text-xs font-bold text-green-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Award size={14} /> Skills I Can Teach
                    </h4>
                    {teachSkills.length === 0 ? (
                      <p className="text-xs text-text-secondary italic">No skills listed</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {teachSkills.map((s) => (
                          <span
                            key={s.id}
                            className="px-2.5 py-1 text-xs font-semibold bg-green-500/10 text-green-600 rounded-md border border-green-500/10"
                          >
                            {s.skill?.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Skills to Learn */}
                  <div>
                    <h4 className="text-xs font-bold text-accent uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <BookOpen size={14} /> Skills I Want to Learn
                    </h4>
                    {learnSkills.length === 0 ? (
                      <p className="text-xs text-text-secondary italic">No skills listed</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {learnSkills.map((s) => (
                          <span
                            key={s.id}
                            className="px-2.5 py-1 text-xs font-semibold bg-accent/10 text-accent rounded-md border border-accent/10"
                          >
                            {s.skill?.name}
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

      {/* Booking Form Modal */}
      <Modal
        isOpen={isBookModalOpen}
        onClose={() => !bookSessionMutation.isPending && setIsBookModalOpen(false)}
        title={`Book Session with ${initialName}`}
        size="md"
        closeOnOverlayClick={!bookSessionMutation.isPending}
      >
        {bookingSuccess ? (
          <div className="py-8 flex flex-col items-center gap-3 text-center">
            <CheckCircle className="text-green-500" size={48} />
            <h3 className="font-bold text-base text-text">Session Booked Successfully!</h3>
            <p className="text-xs text-text-secondary">
              Redirecting you to your sessions list...
            </p>
          </div>
        ) : (
          <form onSubmit={handleBookSubmit} className="flex flex-col gap-4">
            {bookingError && (
              <div className="p-3 text-xs bg-danger/10 border border-danger/20 text-danger rounded-md font-medium flex items-center gap-1.5">
                <AlertCircle size={14} className="shrink-0" />
                <span>{bookingError}</span>
              </div>
            )}

            {/* Select Skill */}
            <div className="flex flex-col gap-1.5 text-left">
              <label htmlFor="select-skill" className="text-xs font-semibold text-text-secondary">
                Select Skill to Learn
              </label>
              <select
                id="select-skill"
                value={selectedSkillId}
                onChange={(e) => setSelectedSkillId(e.target.value)}
                disabled={bookSessionMutation.isPending}
                className="w-full px-3 py-2 text-sm rounded-md border border-border bg-bg text-text shadow-sm focus:outline-none focus:border-accent"
              >
                {teachSkills.length === 0 ? (
                  <option value="">No teaching skills available</option>
                ) : (
                  teachSkills.map((s) => (
                    <option key={s.skill_id} value={s.skill_id}>
                      {s.skill?.name}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Select Date and Time */}
            <div className="flex flex-col gap-1.5 text-left">
              <label htmlFor="select-date" className="text-xs font-semibold text-text-secondary">
                Date & Time
              </label>
              <Input
                id="select-date"
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                disabled={bookSessionMutation.isPending}
              />
            </div>

            {/* Meeting link preview */}
            <div className="p-3 bg-bg-alt border border-border rounded-lg flex items-center justify-between text-xs text-text-secondary mt-1">
              <div className="flex items-center gap-2">
                <Video size={14} className="text-accent" />
                <span>Google Meet/Jitsi Call (Auto-Generated)</span>
              </div>
              <span className="font-semibold text-accent">Active</span>
            </div>

            {/* Coin deduction info */}
            <p className="text-[10px] text-text-secondary mt-2 text-left italic">
              Note: Scheduling a peer-to-peer lesson will deduct 5 Skill Coins from your wallet balance.
            </p>

            {/* Action buttons */}
            <div className="flex justify-end gap-3 mt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsBookModalOpen(false)}
                disabled={bookSessionMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                isLoading={bookSessionMutation.isPending}
                disabled={teachSkills.length === 0}
              >
                Book Swap
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
