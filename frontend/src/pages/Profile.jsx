import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { motion, AnimatePresence } from "motion/react";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import Card from "../components/common/Card";
import SpotlightCard from "../components/common/SpotlightCard";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Textarea from "../components/common/Textarea";
import Avatar from "../components/common/Avatar";
import Modal from "../components/common/Modal";
import Select from "../components/common/Select";
import Badge from "../components/common/Badge";
import SectionHeader from "../components/common/SectionHeader";
import PageTransition from "../components/common/PageTransition";
import EmptyState from "../components/common/EmptyState";
import { useToast } from "../components/common/Toast";
import {
  User,
  Mail,
  MapPin,
  GraduationCap,
  Save,
  Bell,
  Moon,
  Sun,
  Plus,
  X,
  ShieldCheck,
  Award,
  FileCheck,
  Star,
  Sparkles,
  BookOpen,
  Calendar,
  CheckCircle2,
  SlidersHorizontal,
  Settings,
  ArrowRight,
  TrendingUp,
  Clock,
  Video,
  Code2,
} from "lucide-react";
import CredibilityBadge from "../components/verification/CredibilityBadge";
import SkillAssessmentModal from "../components/verification/SkillAssessmentModal";
import MentorAvailabilitySettings from "../components/Mentor/MentorAvailabilitySettings";
import { verificationApi } from "../api/verificationApi";
import { AVATAR_OPTIONS } from "../utils/avatars";


export default function Profile() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const [activeTab, setActiveTab] = useState("overview"); // 'overview', 'skills', 'edit', 'preferences'
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState(false);
  const [skillType, setSkillType] = useState("teach"); // 'teach' or 'learn'
  const [newSkillName, setNewSkillName] = useState("");
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [assessmentSkill, setAssessmentSkill] = useState(null);
  const [selectedAvatar, setSelectedAvatar] = useState(null);

  // 1. Fetch User Credibility Evidence Signals
  const { data: myCredibility, isLoading: isCredibilityLoading } = useQuery({
    queryKey: ["myCredibility"],
    queryFn: () => verificationApi.getMyCredibility(),
  });

  // 2. Fetch User Profile
  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: async () => {
      const res = await api.get("/profiles/me");
      return res.data;
    },
  });

  // 3. Fetch User Skills
  const { data: userSkills = [], isLoading: isSkillsLoading, refetch: refetchUserSkills } = useQuery({
    queryKey: ["userSkills"],
    queryFn: async () => {
      const res = await api.get("/skills/me");
      return res.data;
    },
  });

  // 4. Fetch All Available Skills for Selection
  const { data: allSkills = [] } = useQuery({
    queryKey: ["allSkills"],
    queryFn: async () => {
      const res = await api.get("/skills");
      return res.data;
    },
  });

  const addSkillMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post("/skills/me", data);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Skill added successfully", "Success");
      refetchUserSkills();
      queryClient.invalidateQueries({ queryKey: ["userSkills"] });
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      setIsSkillsModalOpen(false);
      setNewSkillName("");
      setSelectedSkillId("");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to add skill", "Error");
    },
  });

  const removeSkillMutation = useMutation({
    mutationFn: async (skillId) => {
      await api.delete(`/skills/me/${skillId}`);
    },
    onSuccess: () => {
      toast.success("Skill removed successfully", "Success");
      refetchUserSkills();
      queryClient.invalidateQueries({ queryKey: ["userSkills"] });
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to remove skill", "Error");
    },
  });

  const createSkillMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post("/skills", data);
      return res.data;
    },
    onSuccess: (data) => {
      addSkillMutation.mutate({ skill_id: data.id, type: skillType });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to create skill", "Error");
    },
  });

  const handleAddSkill = () => {
    if (selectedSkillId) {
      addSkillMutation.mutate({ skill_id: parseInt(selectedSkillId), type: skillType });
    } else if (newSkillName.trim()) {
      createSkillMutation.mutate({ name: newSkillName.trim(), category: "general" });
    }
  };

  const handleRemoveSkill = (userSkillId) => {
    removeSkillMutation.mutate(userSkillId);
  };

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    defaultValues: {
      name: user?.name || "",
      email: user?.email || "",
      bio: "",
      department: "",
      year: "",
    },
  });

  useEffect(() => {
    if (profile || user) {
      reset({
        name: user?.name || "",
        email: user?.email || "",
        bio: profile?.bio || "",
        department: profile?.department || "",
        year: profile?.year || "",
      });
    }
  }, [profile, user, reset]);

  const updateProfileMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.put("/profiles/me", data);
      return res.data;
    },
    onSuccess: (data) => {
      if (data.avatar_url) {
        updateUser({ avatar_url: data.avatar_url });
      }
      toast.success("Profile updated successfully", "Success");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      setActiveTab("overview");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update profile", "Error");
    },
  });

  const onSubmit = (data) => {
    const payload = {
      bio: data.bio,
      department: data.department,
      year: data.year ? parseInt(data.year) : null,
      avatar_url: selectedAvatar ? selectedAvatar.url : profile?.avatar_url,
    };
    updateProfileMutation.mutate(payload);
  };

  const teachSkills = userSkills.filter((s) => s.type === "teach");
  const learnSkills = userSkills.filter((s) => s.type === "learn");
  const unverifiedSkills = teachSkills.filter(
    (s) => s.verification_status === "CLAIMED" || !s.verification_status
  );

  return (
    <PageTransition className="space-y-8 text-left max-w-6xl mx-auto">
      {/* Section Header */}
      <SectionHeader
        badge="Credentials Studio"
        badgeIcon={ShieldCheck}
        title="Profile & Verified Credibility"
        subtitle="Manage your identity, test your expertise with 10-question peer evaluations, and configure your mentoring availability."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSkillType("teach");
                setIsSkillsModalOpen(true);
              }}
              leftIcon={Plus}
            >
              Add Teachable Skill
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setActiveTab("edit")}
              leftIcon={Settings}
              className="shadow-glow"
            >
              Edit Profile Info
            </Button>
          </div>
        }
      />

      {/* Advanced Profile Identity Hero with Pushpin */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-visible rounded-3xl bg-card-bg border border-card-border p-6 sm:p-8 shadow-md"
      >
        <div className="absolute -top-3 left-8">
          <div className="w-5 h-5 rounded-full bg-purple-500 shadow-md border-2 border-white ring-1 ring-black/10 flex items-center justify-center relative">
            <div className="w-1.5 h-1.5 rounded-full bg-white/90 absolute top-0.5 left-1" />
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center md:items-start justify-between gap-6 relative z-10 pt-1">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 text-center sm:text-left">
            <div className="relative shrink-0">
              <Avatar
                src={user?.avatar_url}
                alt={user?.name || "User"}
                size="2xl"
                className="ring-4 ring-accent/25 shadow-lg"
              />
              <div className="absolute -bottom-1 -right-1 bg-emerald-500 text-white rounded-full p-1.5 border-2 border-bg shadow-sm">
                <CheckCircle2 size={13} />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
                <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-text">
                  {user?.name || "Student Learner"}
                </h1>
                {myCredibility && (
                  <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-accent/15 text-accent border border-accent/25">
                    Score {myCredibility.overall_credibility_score}/100
                  </span>
                )}
              </div>
              <p className="text-xs sm:text-sm font-semibold text-text-secondary">
                {profile?.department ? `${profile.department} Student` : "Computer Science & Engineering"} • Year {profile?.year || 1}
              </p>
              <p className="text-xs text-text-muted flex items-center justify-center sm:justify-start gap-1">
                <Mail size={13} /> {user?.email}
              </p>
              {profile?.bio && (
                <p className="text-xs text-text-secondary italic max-w-xl pt-1 line-clamp-2">
                  &ldquo;{profile.bio}&rdquo;
                </p>
              )}
            </div>
          </div>

          {/* Quick Credibility Summary Matrix */}
          <div className="grid grid-cols-3 gap-3 shrink-0 w-full md:w-auto text-center">
            <div className="p-3.5 rounded-2xl bg-bg-alt border border-border/80 shadow-xs">
              <span className="text-[10px] font-bold text-text-muted uppercase block">Verified Skills</span>
              <span className="text-xl font-black text-emerald-600 dark:text-emerald-400 mt-0.5 block">
                {myCredibility?.verified_skills_count ?? teachSkills.filter(s => s.verification_status === "VERIFIED").length}
              </span>
            </div>
            <div className="p-3.5 rounded-2xl bg-bg-alt border border-border/80 shadow-xs">
              <span className="text-[10px] font-bold text-text-muted uppercase block">Completed Sessions</span>
              <span className="text-xl font-black text-accent mt-0.5 block">
                {myCredibility?.total_completed_sessions ?? 0}
              </span>
            </div>
            <div className="p-3.5 rounded-2xl bg-bg-alt border border-border/80 shadow-xs">
              <span className="text-[10px] font-bold text-text-muted uppercase block">Average Rating</span>
              <span className="text-xl font-black text-amber-500 mt-0.5 block flex items-center justify-center gap-0.5">
                <Star size={16} className="fill-amber-500" />
                {myCredibility?.overall_average_rating ? Number(myCredibility.overall_average_rating).toFixed(1) : "5.0"}
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Navigation Tab Bar */}
      <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-surface-elevated border border-border w-fit shadow-xs overflow-x-auto">
        {[
          { id: "overview", label: "Credentials & Signals", icon: ShieldCheck },
          { id: "skills", label: `Teachable & Learning Skills (${userSkills.length})`, icon: Award },
          { id: "availability", label: "Mentor Availability", icon: Calendar },
          { id: "edit", label: "Edit Profile Details", icon: User },
          { id: "preferences", label: "Preferences & Theme", icon: Settings },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-180 whitespace-nowrap cursor-pointer ${
                isActive
                  ? "bg-accent text-white shadow-glow"
                  : "text-text-secondary hover:text-text hover:bg-bg-alt"
              }`}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>


      {/* Tab 1: Overview & Verification Signals */}
      {activeTab === "overview" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Skill Verification Hub Banner */}
          <div className="bg-gradient-to-r from-emerald-600 via-accent to-purple-700 p-6 sm:p-8 rounded-3xl text-white shadow-xl flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden">
            <div className="flex items-start gap-4 z-10">
              <div className="p-3.5 bg-white/20 backdrop-blur-md rounded-2xl text-white shadow-inner shrink-0">
                <ShieldCheck size={32} />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <h2 className="text-xl sm:text-2xl font-black tracking-tight">Peer Verification Studio</h2>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase bg-white/20 backdrop-blur-sm text-white border border-white/30">
                    Active Evaluations
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-white/90 max-w-xl leading-relaxed">
                  {unverifiedSkills.length > 0
                    ? `You have ${unverifiedSkills.length} unverified skill(s). Complete the 10-question evaluation to unlock Verified Credibility signals across mentor discovery feeds!`
                    : teachSkills.length === 0
                    ? "Add a skill you can teach to unlock 10-question evaluations and establish credibility."
                    : "All your teaching skills are verified! Retake evaluations anytime to boost your score ranking."}
                </p>
              </div>
            </div>

            <div className="shrink-0 z-10 w-full md:w-auto flex justify-end">
              {unverifiedSkills.length > 0 ? (
                <Button
                  variant="ghost"
                  size="md"
                  className="bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-text border border-white/30 shadow-xl px-5 py-2.5 text-sm cursor-pointer w-full md:w-auto font-black"
                  onClick={() =>
                    setAssessmentSkill({
                      id: unverifiedSkills[0].skill_id,
                      name: unverifiedSkills[0].skill?.name || unverifiedSkills[0].name,
                    })
                  }
                >
                  <Sparkles size={16} className="mr-2 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  <span>Verify &ldquo;{unverifiedSkills[0].skill?.name || unverifiedSkills[0].name}&rdquo; (10 Qs)</span>
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="md"
                  className="bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-text border border-white/30 shadow-xl px-5 py-2.5 text-sm cursor-pointer w-full md:w-auto font-black"
                  onClick={() => {
                    setSkillType("teach");
                    setIsSkillsModalOpen(true);
                  }}
                >
                  <Plus size={16} className="mr-2 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  <span>Add Skill to Verify</span>
                </Button>
              )}
            </div>
          </div>

          {/* Credibility Signals Breakdown Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Credibility Tier Breakdown" subtitle="How your platform reputation is calculated">
              <div className="space-y-4">
                <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-3">
                  <ShieldCheck size={20} className="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-xs text-text">Tier 1: Verified Mentor</h4>
                    <p className="text-[11px] text-text-secondary mt-0.5">
                      Achieved by scoring 70%+ on the 10-question algorithmic skill assessment.
                    </p>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-start gap-3">
                  <Award size={20} className="text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-xs text-text">Tier 2: Trusted Peer</h4>
                    <p className="text-[11px] text-text-secondary mt-0.5">
                      Earned through 5+ completed sessions with an average feedback rating of 4.5+.
                    </p>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-3">
                  <Star size={20} className="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-xs text-text">Tier 3: Claimed Competency</h4>
                    <p className="text-[11px] text-text-secondary mt-0.5">
                      Self-declared skills ready for peer assessment verification.
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Live Server Signals" subtitle="Real-time evidence metrics registered on your profile">
              <div className="space-y-3 pt-1 text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-bg border border-border/80">
                  <span className="text-text-secondary font-medium">Total Teachable Skills:</span>
                  <span className="font-extrabold text-text">{teachSkills.length}</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-bg border border-border/80">
                  <span className="text-text-secondary font-medium">Verified Skills Count:</span>
                  <span className="font-extrabold text-emerald-600 dark:text-emerald-400">
                    {teachSkills.filter(s => s.verification_status === "VERIFIED" || s.verification_status === "TRUSTED").length}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-bg border border-border/80">
                  <span className="text-text-secondary font-medium">Completed Mentorship Sessions:</span>
                  <span className="font-extrabold text-accent">{myCredibility?.total_completed_sessions ?? 0}</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-bg border border-border/80">
                  <span className="text-text-secondary font-medium">Total Reviews Received:</span>
                  <span className="font-extrabold text-text">{myCredibility?.total_feedback_count ?? 0}</span>
                </div>
              </div>
            </Card>
          </div>
        </motion.div>
      )}

      {/* Tab 2: Skills Inventory & Assessments */}
      {activeTab === "skills" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Teachable Skills Section */}
          <Card
            title="Teachable Skills & Assessments"
            subtitle="Skills you offer to other students with verification status"
            footer={
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSkillType("teach");
                  setIsSkillsModalOpen(true);
                }}
                leftIcon={Plus}
              >
                Add Another Teachable Skill
              </Button>
            }
          >
            {teachSkills.length === 0 ? (
              <EmptyState
                icon={Award}
                title="No teachable skills added yet"
                description="Add your technical strengths so compatible peers can discover you and request mentoring sessions."
                actionLabel="Add Skill"
                onAction={() => {
                  setSkillType("teach");
                  setIsSkillsModalOpen(true);
                }}
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {teachSkills.map((s) => {
                  const sName = s.skill?.name || s.name;
                  const status = s.verification_status || "CLAIMED";
                  const isVerified = status === "VERIFIED" || status === "TRUSTED";

                  return (
                    <div
                      key={s.id}
                      className={`p-4 rounded-2xl border flex flex-col justify-between gap-3 transition-all ${
                        isVerified
                          ? "bg-emerald-500/5 border-emerald-500/25"
                          : "bg-surface-elevated border-border"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="font-bold text-sm text-text">{sName}</h4>
                          <span className="text-[11px] text-text-secondary mt-0.5 block">
                            Category: {s.skill?.category || "Technical"}
                          </span>
                        </div>
                        <CredibilityBadge status={status} score={s.score} size="sm" />
                      </div>

                      <div className="flex items-center justify-between gap-2 pt-2 border-t border-border/60">
                        <Button
                          variant={isVerified ? "outline" : "primary"}
                          size="xs"
                          className={
                            isVerified
                              ? "text-xs font-semibold"
                              : "bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold shadow-sm"
                          }
                          onClick={() =>
                            setAssessmentSkill({
                              id: s.skill_id,
                              name: sName,
                            })
                          }
                        >
                          <FileCheck size={13} className="mr-1" />
                          {isVerified ? "Retake (10 Qs)" : "Verify Skill (10 Qs)"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="xs"
                          className="text-text-secondary hover:text-danger p-1"
                          onClick={() => handleRemoveSkill(s.id)}
                        >
                          <X size={14} />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Learning Goals Section */}
          <Card
            title="Learning Goals & Target Skills"
            subtitle="Skills you want to master through peer sessions and roadmaps"
            footer={
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSkillType("learn");
                  setIsSkillsModalOpen(true);
                }}
                leftIcon={Plus}
              >
                Add Learning Goal
              </Button>
            }
          >
            {learnSkills.length === 0 ? (
              <EmptyState
                icon={BookOpen}
                title="No learning goals added yet"
                description="Specify what you want to learn to get matched with peer experts automatically."
                actionLabel="Add Learning Goal"
                onAction={() => {
                  setSkillType("learn");
                  setIsSkillsModalOpen(true);
                }}
              />
            ) : (
              <div className="flex flex-wrap gap-2 pt-1">
                {learnSkills.map((s) => (
                  <Badge
                    key={s.id}
                    variant="accent"
                    removable={true}
                    onClose={() => handleRemoveSkill(s.id)}
                    className="px-3.5 py-1.5 text-xs font-bold"
                  >
                    {s.skill?.name || s.name}
                  </Badge>
                ))}
              </div>
            )}
          </Card>
        </motion.div>
      )}

      {/* Tab 3: Edit Profile Info */}
      {activeTab === "edit" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <Card title="Edit Profile Information" subtitle="Update your academic and personal details">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {/* Avatar Selector */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-text-secondary">
                  Choose Avatar Style
                </label>
                <div className="grid grid-cols-6 gap-2.5 p-3 bg-bg-alt/70 rounded-2xl border border-border/80">
                  {AVATAR_OPTIONS.map((avatar) => {
                    const isCurrent =
                      (selectedAvatar && selectedAvatar.id === avatar.id) ||
                      (!selectedAvatar && user?.avatar_url === avatar.url);

                    return (
                      <button
                        key={avatar.id}
                        type="button"
                        onClick={() => setSelectedAvatar(avatar)}
                        className={`
                          relative w-full aspect-square rounded-full overflow-hidden
                          transition-all duration-150 cursor-pointer
                          ${
                            isCurrent
                              ? "ring-3 ring-accent ring-offset-2 ring-offset-bg scale-110 shadow-glow"
                              : "hover:scale-105 opacity-65 hover:opacity-100"
                          }
                        `}
                      >
                        <img
                          src={avatar.url}
                          alt={avatar.emoji}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    );
                  })}
                </div>
              </div>

              <Input
                label="Full Name"
                icon={<User size={16} />}
                {...register("name")}
                disabled={true}
              />

              <Input
                label="Email Address"
                type="email"
                icon={<Mail size={16} />}
                {...register("email")}
                disabled={true}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Department / Program"
                  icon={<MapPin size={16} />}
                  placeholder="e.g. Computer Science"
                  {...register("department")}
                  disabled={isSubmitting}
                />

                <Input
                  label="Academic Year"
                  type="number"
                  min="1"
                  max="6"
                  placeholder="e.g. 3"
                  {...register("year", {
                    valueAsNumber: true,
                    min: { value: 1, message: "Year must be at least 1" },
                    max: { value: 6, message: "Year must be at most 6" },
                  })}
                  error={errors.year?.message}
                  disabled={isSubmitting}
                />
              </div>

              <Textarea
                label="Bio & Engineering Specialties"
                placeholder="Tell peers what frameworks, languages, and topics you enjoy exploring..."
                rows={4}
                {...register("bio")}
                disabled={isSubmitting}
              />

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab("overview")}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isSubmitting}
                  loading={isSubmitting}
                  leftIcon={Save}
                  className="shadow-glow"
                >
                  Save Profile
                </Button>
              </div>
            </form>
          </Card>
        </motion.div>
      )}

      {/* Tab 3: Mentor Availability */}
      {activeTab === "availability" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <MentorAvailabilitySettings />
        </motion.div>
      )}

      {/* Tab 4: Preferences & Theme */}
      {activeTab === "preferences" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <Card title="Account & Appearance Preferences" subtitle="Customize your app experience">

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-bg border border-border rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-emerald-500/10 text-emerald-500 rounded-xl border border-emerald-500/20">
                    <CheckCircle2 size={18} />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-text">Open for Peer Swap Sessions</p>
                    <p className="text-xs text-text-secondary">Allow peers to book 1-on-1 sessions with you</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-9 h-5 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent" />
                </label>
              </div>

              <div className="flex items-center justify-between p-4 bg-bg border border-border rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-accent/10 text-accent rounded-xl border border-accent/20">
                    <Bell size={18} />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-text">Session Notification Reminders</p>
                    <p className="text-xs text-text-secondary">Receive real-time notifications before scheduled calls</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-9 h-5 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent" />
                </label>
              </div>

              <div className="flex items-center justify-between p-4 bg-bg border border-border rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-purple-500/10 text-purple-500 rounded-xl border border-purple-500/20">
                    <Moon size={18} />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-text">Dark Mode Theme</p>
                    <p className="text-xs text-text-secondary">Toggle high-contrast dark theme</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={document.documentElement.classList.contains("dark")}
                    onChange={(e) => {
                      const root = document.documentElement;
                      if (e.target.checked) {
                        root.classList.add("dark");
                        root.classList.remove("light");
                        localStorage.setItem("theme", "dark");
                      } else {
                        root.classList.add("light");
                        root.classList.remove("dark");
                        localStorage.setItem("theme", "light");
                      }
                    }}
                  />
                  <div className="w-9 h-5 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent" />
                </label>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Add Skill Modal */}
      <Modal
        isOpen={isSkillsModalOpen}
        onClose={() => {
          setIsSkillsModalOpen(false);
          setNewSkillName("");
          setSelectedSkillId("");
        }}
        title={`Add ${skillType === "teach" ? "Teachable" : "Learning"} Skill`}
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-text-secondary mb-2">
              Select from platform catalog
            </label>
            <Select
              placeholder="Choose a skill..."
              options={allSkills.map((skill) => ({
                value: skill.id.toString(),
                label: skill.name,
              }))}
              value={selectedSkillId}
              onChange={(value) => {
                setSelectedSkillId(value);
                setNewSkillName("");
              }}
              disabled={!!newSkillName}
            />
          </div>

          <div className="flex items-center gap-2">
            <div className="flex-1 h-px bg-border" />
            <span className="text-xs text-text-secondary">or</span>
            <div className="flex-1 h-px bg-border" />
          </div>

          <div>
            <label className="block text-xs font-bold text-text-secondary mb-2">
              Create a custom skill
            </label>
            <Input
              placeholder="Enter skill name (e.g. Next.js 15, FastAPI, PyTorch)..."
              value={newSkillName}
              onChange={(e) => {
                setNewSkillName(e.target.value);
                setSelectedSkillId("");
              }}
              disabled={!!selectedSkillId}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsSkillsModalOpen(false);
                setNewSkillName("");
                setSelectedSkillId("");
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleAddSkill}
              disabled={!selectedSkillId && !newSkillName.trim()}
              loading={addSkillMutation.isPending || createSkillMutation.isPending}
            >
              Add to Profile
            </Button>
          </div>
        </div>
      </Modal>

      {/* Skill Assessment Modal */}
      {assessmentSkill && (
        <SkillAssessmentModal
          isOpen={!!assessmentSkill}
          onClose={() => {
            setAssessmentSkill(null);
            refetchUserSkills();
            queryClient.invalidateQueries(["myCredibility"]);
          }}
          skillId={assessmentSkill.id}
          skillName={assessmentSkill.name}
        />
      )}
    </PageTransition>
  );
}
