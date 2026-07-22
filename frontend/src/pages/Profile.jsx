import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Textarea from "../components/common/Textarea";
import Avatar from "../components/common/Avatar";
import Modal from "../components/common/Modal";
import Select from "../components/common/Select";
import Badge from "../components/common/Badge";
import { useToast } from "../components/common/Toast";
import { User, Mail, MapPin, GraduationCap, Save, Bell, Moon, Sun, Plus, X, Search } from "lucide-react";
import StreakCard from "../components/streak/StreakCard";
import { useStreak } from "../hooks/useStreak";
import MilestoneCard from "../components/streak/MilestoneCard";

export default function Profile() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState(false);
  const [skillType, setSkillType] = useState("teach"); // 'teach' or 'learn'
  const [newSkillName, setNewSkillName] = useState("");
  const [selectedSkillId, setSelectedSkillId] = useState("");

  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: async () => {
      const res = await api.get("/profiles/me");
      return res.data;
    },
  });

  const { data: userSkills = [], isLoading: isSkillsLoading, refetch: refetchUserSkills } = useQuery({
    queryKey: ["userSkills"],
    queryFn: async () => {
      const res = await api.get("/skills/me");
      return res.data;
    },
  });

  const { data: allSkills = [] } = useQuery({
    queryKey: ["allSkills"],
    queryFn: async () => {
      const res = await api.get("/skills");
      return res.data;
    },
  });
  // Fetch streak analytics
  const { data: streakData, isLoading: streakLoading, isError: streakError, refetch: refetchStreak } = useStreak();

  const addSkillMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post("/skills/me", data);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Skill added successfully", "Success");
      refetchUserSkills();
      queryClient.invalidateQueries(["userSkills"]);
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
      queryClient.invalidateQueries(["userSkills"]);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to remove skill", "Error");
    },
  });

  const createSkillMutation = useMutation({
    mutationFn: async (data) => {
      console.log("Creating skill:", data);
      const res = await api.post("/skills", data);
      console.log("Skill created:", res.data);
      return res.data;
    },
    onSuccess: (data) => {
      console.log("Skill creation success, adding to user skills:", data);
      // After creating the skill, add it to user's skills
      addSkillMutation.mutate({ skill_id: data.id, type: skillType });
    },
    onError: (error) => {
      console.error("Skill creation error:", error);
      toast.error(error.response?.data?.detail || "Failed to create skill", "Error");
    },
  });

  const handleAddSkill = () => {
    console.log("handleAddSkill called:", { selectedSkillId, newSkillName, skillType });
    if (selectedSkillId) {
      console.log("Adding existing skill:", { skill_id: parseInt(selectedSkillId), type: skillType });
      addSkillMutation.mutate({ skill_id: parseInt(selectedSkillId), type: skillType });
    } else if (newSkillName.trim()) {
      console.log("Creating new skill:", { name: newSkillName.trim(), category: "general" });
      createSkillMutation.mutate({ name: newSkillName.trim(), category: "general" });
    } else {
      console.log("No skill selected or entered");
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
      queryClient.invalidateQueries(["profile"]);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update profile", "Error");
    },
  });

  const onSubmit = (data) => {
    // Only send fields that backend accepts
    const payload = {
      bio: data.bio,
      department: data.department,
      year: data.year ? parseInt(data.year) : null,
      avatar_url: profile?.avatar_url,
    };
    updateProfileMutation.mutate(payload);
  };

  const teachSkills = userSkills.filter((s) => s.type === "teach");
  const learnSkills = userSkills.filter((s) => s.type === "learn");

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Profile & Settings</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage your personal information and app preferences
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Profile Card */}
        <div className="lg:col-span-1">
          <Card className="text-center">
            <div className="flex flex-col items-center gap-4">
              <Avatar src={user?.avatar_url} alt={user?.name || "User"} size="xl" />
              <div>
                <h2 className="text-lg font-semibold text-text">{user?.name || "User"}</h2>
                <p className="text-sm text-text-secondary">{user?.email}</p>
              </div>
              <div className="w-full h-px bg-border" />
              <div className="w-full text-left space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <GraduationCap size={16} className="text-text-secondary" />
                  <span className="text-text-secondary">
                    {profile?.department ? `${profile.department} - Year ${profile.year}` : "Not set"}
                  </span>
                </div>
                {profile?.bio && (
                  <div className="flex items-start gap-2 text-sm">
                    <User size={16} className="text-text-secondary mt-0.5" />
                    <p className="text-text-secondary italic line-clamp-3">"{profile.bio}"</p>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Learning Streak */}
<StreakCard />
{streakData && (
  <MilestoneCard
    currentMilestone={streakData.current_milestone}
    nextMilestone={streakData.next_milestone}
    remainingDays={streakData.remaining_days}
    progressPercentage={streakData.progress_percentage}
  />
)}
{/* Skills Summary */}
          <Card title="Your Skills" className="mt-6">
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Teaching ({teachSkills.length})
                  </h3>
                  <Button
                    variant="ghost"
                    size="xs"
                    onClick={() => {
                      setSkillType("teach");
                      setIsSkillsModalOpen(true);
                    }}
                  >
                    <Plus size={12} className="mr-1" />
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {isSkillsLoading ? (
                    <div className="h-6 w-20 bg-border/40 animate-pulse rounded-full" />
                  ) : teachSkills.length === 0 ? (
                    <span className="text-xs text-text-secondary italic">None</span>
                  ) : (
                    teachSkills.map((s) => (
                      <Badge
                        key={s.id}
                        variant="success"
                        removable={true}
                        onClose={() => handleRemoveSkill(s.id)}
                      >
                        {s.skill?.name || s.name}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Learning ({learnSkills.length})
                  </h3>
                  <Button
                    variant="ghost"
                    size="xs"
                    onClick={() => {
                      setSkillType("learn");
                      setIsSkillsModalOpen(true);
                    }}
                  >
                    <Plus size={12} className="mr-1" />
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {isSkillsLoading ? (
                    <div className="h-6 w-20 bg-border/40 animate-pulse rounded-full" />
                  ) : learnSkills.length === 0 ? (
                    <span className="text-xs text-text-secondary italic">None</span>
                  ) : (
                    learnSkills.map((s) => (
                      <Badge
                        key={s.id}
                        variant="accent"
                        removable={true}
                        onClose={() => handleRemoveSkill(s.id)}
                      >
                        {s.skill?.name || s.name}
                      </Badge>
                    ))
                  )}
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - Edit Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="Edit Profile" subtitle="Update your personal information">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Input
                label="Full Name"
                icon={<User size={16} />}
                {...register("name")}
                disabled={true}
              />

              <Input
                label="Email"
                type="email"
                icon={<Mail size={16} />}
                {...register("email")}
                disabled={true}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Department"
                  icon={<MapPin size={16} />}
                  {...register("department")}
                  disabled={isSubmitting}
                />

                <Input
                  label="Year"
                  type="number"
                  min="1"
                  max="6"
                  {...register("year", { 
                    valueAsNumber: true,
                    min: { value: 1, message: "Year must be at least 1" },
                    max: { value: 6, message: "Year must be at most 6" }
                  })}
                  error={errors.year?.message}
                  disabled={isSubmitting}
                />
              </div>

              <Textarea
                label="Bio"
                placeholder="Tell us about yourself..."
                rows={4}
                {...register("bio")}
                disabled={isSubmitting}
              />

              <div className="flex justify-end gap-2 pt-2">
                <Button 
                  type="submit" 
                  variant="primary" 
                  size="sm"
                  disabled={isSubmitting}
                  loading={isSubmitting}
                >
                  <Save size={16} className="mr-2" />
                  Save Changes
                </Button>
              </div>
            </form>
          </Card>

          {/* App Settings */}
          <Card title="App Settings" subtitle="Configure your preferences">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-bg border border-border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-accent/10 text-accent rounded-lg">
                    <Bell size={16} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text">Email Notifications</p>
                    <p className="text-xs text-text-secondary">Receive session reminders and updates</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-9 h-5 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent" />
                </label>
              </div>

              <div className="flex items-center justify-between p-3 bg-bg border border-border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-accent/10 text-accent rounded-lg">
                    <Moon size={16} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text">Dark Mode</p>
                    <p className="text-xs text-text-secondary">Toggle dark theme (also in header)</p>
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
        </div>
      </div>

      {/* Add Skill Modal */}
      <Modal
        isOpen={isSkillsModalOpen}
        onClose={() => {
          setIsSkillsModalOpen(false);
          setNewSkillName("");
          setSelectedSkillId("");
        }}
        title={`Add ${skillType === "teach" ? "Teaching" : "Learning"} Skill`}
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Select from existing skills
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
            <label className="block text-sm font-medium text-text mb-2">
              Create a new skill
            </label>
            <Input
              placeholder="Enter skill name..."
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
              Add Skill
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
