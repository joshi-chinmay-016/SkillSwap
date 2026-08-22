import React, { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm, Controller } from "react-hook-form";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Select from "../components/common/Select";
import { useToast } from "../components/common/Toast";
import AILoadingScreen from "../components/common/AILoadingScreen";
import {
  Sparkles,
  MapPin,
  CheckCircle,
  Circle,
  Clock,
  ArrowRight,
  BookOpen,
  Target,
  ArrowUp,
  ArrowDown,
  Compass,
  Code2,
  CheckCircle2,
  Layers,
} from "lucide-react";

export default function Roadmap() {
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [roadmap, setRoadmap] = useState(null);
  const [roadmapRequestSnapshot, setRoadmapRequestSnapshot] = useState(null);
  const [selectedWeek, setSelectedWeek] = useState(null);
  const [showForm, setShowForm] = useState(false);

  // Check if forcing a new journey build via '?new=true'
  const queryParams = new URLSearchParams(location.search);
  const isForceNew = queryParams.get("new") === "true";

  // Query for active journey
  const { data: activeJourney, isLoading: isLoadingActive } = useQuery({
    queryKey: ["journeys", "active"],
    queryFn: async () => {
      const res = await api.get("/journeys/me/active");
      return res.data;
    },
    enabled: !isForceNew,
  });

  // Redirect if active journey exists and we're not forcing new
  useEffect(() => {
    if (activeJourney && !isForceNew) {
      navigate(`/journey/${activeJourney.id}`, { replace: true });
    }
  }, [activeJourney, isForceNew, navigate]);

  // Fetch user's skills for the form
  const { data: userSkills = [] } = useQuery({
    queryKey: ["skills", "me"],
    queryFn: async () => {
      const res = await api.get("/skills/me");
      return res.data;
    },
  });

  const profileSkillNames = userSkills
    .map((s) => s.skill?.name || s.name)
    .filter(Boolean);

  const {
    control,
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: {
      target_role: "",
      custom_skills: "",
      experience_level: "Beginner",
      duration_months: "3",
    },
  });

  useEffect(() => {
    if (profileSkillNames.length > 0) {
      setValue("custom_skills", profileSkillNames.join(", "));
    }
  }, [profileSkillNames.length, setValue]);

  const roadmapMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post("/ai/roadmap", data);
      return res.data;
    },
    onSuccess: (data) => {
      setRoadmap(data);
      toast.success("Roadmap generated successfully!", "Success");
    },
    onError: (error) => {
      console.error("Roadmap error:", error);
      toast.error(
        error.response?.data?.detail || "Failed to generate roadmap. Please try again.",
        "Error"
      );
    },
  });

  const validateRoadmap = (rm) => {
    if (!rm || !rm.title || !Array.isArray(rm.weeks) || rm.weeks.length === 0) return false;
    return rm.weeks.every(
      (w) =>
        typeof w.week === "number" &&
        typeof w.topic === "string" &&
        w.topic.trim().length > 0
    );
  };

  const saveJourneyMutation = useMutation({
    mutationFn: async () => {
      if (!roadmap || !roadmapRequestSnapshot) return;

      const payload = {
        title: roadmap.title,
        target_role: roadmapRequestSnapshot.target_role,
        description: null,
        duration_months: roadmapRequestSnapshot.duration_months,
        weeks: roadmap.weeks.map((w) => ({
          week: w.week,
          topic: w.topic,
          goal: w.goal || `Complete week ${w.week} milestones`,
          tasks: (w.tasks || []).map((t) => ({
            title: t.title,
            description: t.description || "",
            resources: Array.isArray(t.resources) ? t.resources : [],
          })),
        })),
      };

      const res = await api.post("/journeys", payload);
      return res.data;
    },
    onSuccess: (data) => {
      toast.success("Learning Journey saved successfully!", "Success");
      queryClient.invalidateQueries({ queryKey: ["journeys"] });
      queryClient.invalidateQueries({ queryKey: ["journeys", "active"] });
      navigate(`/journey/${data.id}`);
    },
    onError: (error) => {
      console.error("Save journey error:", error);
      toast.error(
        error.response?.data?.detail || "Failed to save learning journey",
        "Error"
      );
    },
  });

  const handleSaveJourney = () => {
    if (!validateRoadmap(roadmap)) {
      toast.error(
        "The generated roadmap is incomplete. Please regenerate.",
        "Invalid Roadmap"
      );
      return;
    }
    saveJourneyMutation.mutate();
  };

  const onSubmit = (data) => {
    let currentSkillsList = [];
    if (data.custom_skills && data.custom_skills.trim().length > 0) {
      currentSkillsList = data.custom_skills
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
    } else {
      currentSkillsList = profileSkillNames;
    }

    if (currentSkillsList.length === 0) {
      currentSkillsList = ["Beginner Fundamentals"];
    }

    const payload = {
      current_skills: currentSkillsList,
      target_role: data.target_role,
      experience_level: data.experience_level,
      duration_months: parseInt(data.duration_months, 10) || 3,
    };

    setRoadmapRequestSnapshot(payload);
    roadmapMutation.mutate(payload);
  };

  if (isLoadingActive && !isForceNew) {
    return (
      <div className="flex flex-col gap-4 max-w-4xl mx-auto p-4">
        <div className="h-12 w-48 bg-border/40 animate-pulse rounded-lg" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 w-full bg-border/40 animate-pulse rounded-2xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto text-left">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">AI Roadmap Builder</h1>
          <p className="text-xs text-text-secondary mt-1">
            Generate a personalized, milestone-driven learning journey for any career goal
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate("/journey/skill-gap")}
          leftIcon={Target}
          className="text-xs font-bold"
        >
          Analyze Skill Gap
        </Button>
      </div>

      {/* Empty State when no active journey and no roadmap generated yet */}
      {!roadmap && !roadmapMutation.isPending && !showForm && (
        <Card className="text-center py-12 flex flex-col items-center justify-center border-dashed border-2 border-border max-w-2xl mx-auto w-full">
          <div className="p-4 bg-accent/10 text-accent rounded-2xl mb-4">
            <Compass size={36} className="animate-spin-slow" />
          </div>
          <h2 className="text-lg font-bold tracking-tight text-text">Your learning journey starts here</h2>
          <p className="text-xs text-text-secondary mt-2 max-w-md leading-relaxed">
            Generate a custom AI roadmap tailored to your experience, duration, and target role. Track week-by-week progress and earn XP milestones.
          </p>
          <div className="mt-6 flex gap-3">
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowForm(true)}
              leftIcon={Sparkles}
              className="font-bold text-xs shadow-glow"
            >
              Generate AI Roadmap
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/profile")}
              className="text-xs font-bold"
            >
              Explore Skills
            </Button>
          </div>
        </Card>
      )}

      {/* Input Form */}
      {!roadmap && !roadmapMutation.isPending && showForm && (
        <Card title="Generate Your Roadmap" subtitle="Define your target learning goals" className="!overflow-visible">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Target Role / Goal"
              placeholder="e.g., Full Stack Engineer, Data Scientist, DevOps Specialist"
              icon={<BookOpen size={16} />}
              {...register("target_role", { required: "Please enter a target role" })}
              error={errors.target_role?.message}
              disabled={isSubmitting}
            />

            <Input
              label="Current Skills (Comma-separated, optional)"
              placeholder="e.g., Python, HTML, CSS, JavaScript"
              icon={<Code2 size={16} />}
              {...register("custom_skills")}
              disabled={isSubmitting}
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Controller
                name="experience_level"
                control={control}
                rules={{ required: "Please select experience level" }}
                render={({ field }) => (
                  <Select
                    label="Experience Level"
                    options={[
                      { value: "Beginner", label: "Beginner (New to the field)" },
                      { value: "Intermediate", label: "Intermediate (Some practical experience)" },
                      { value: "Advanced", label: "Advanced (Looking for deep mastery)" },
                    ]}
                    value={field.value}
                    onChange={field.onChange}
                    error={errors.experience_level?.message}
                    disabled={isSubmitting}
                  />
                )}
              />

              <Controller
                name="duration_months"
                control={control}
                rules={{ required: "Please select duration" }}
                render={({ field }) => (
                  <Select
                    label="Target Duration"
                    options={[
                      { value: "1", label: "1 Month (Intensive Sprint - 4 Weeks)" },
                      { value: "3", label: "3 Months (Standard Quarter - 12 Weeks)" },
                      { value: "6", label: "6 Months (Comprehensive - 24 Weeks)" },
                    ]}
                    value={field.value}
                    onChange={field.onChange}
                    error={errors.duration_months?.message}
                    disabled={isSubmitting}
                  />
                )}
              />
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={isSubmitting}
                isLoading={roadmapMutation.isPending}
                leftIcon={Sparkles}
                className="flex-1 font-bold text-xs shadow-glow"
              >
                Generate Roadmap
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() => setShowForm(false)}
                className="text-xs font-bold"
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Animated Loading screen */}
      {roadmapMutation.isPending && (
        <AILoadingScreen
          isOpen={true}
          type="roadmap"
          title="Building Learning Roadmap"
          onCancel={() => roadmapMutation.reset()}
        />
      )}

      {/* Roadmap Display */}
      {roadmap && !roadmapMutation.isPending && (
        <>
          {/* Review & Save Summary Card */}
          <Card className="bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-xs font-extrabold text-accent uppercase tracking-wider">
                  AI Generated Roadmap
                </span>
                <h2 className="text-lg font-bold text-text mt-0.5">{roadmap.title || "Learning Roadmap"}</h2>
                <p className="text-xs text-text-secondary mt-1">
                  {roadmap.weeks?.length || 0} weeks structured • Save as your active journey to track progress
                </p>
              </div>
              <div className="flex items-center gap-2 self-start sm:self-auto">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSaveJourney}
                  disabled={saveJourneyMutation.isPending}
                  isLoading={saveJourneyMutation.isPending}
                  leftIcon={CheckCircle2}
                  className="font-bold text-xs shadow-glow"
                >
                  Save as Learning Journey
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={saveJourneyMutation.isPending}
                  onClick={() => {
                    setRoadmap(null);
                    setRoadmapRequestSnapshot(null);
                    setSelectedWeek(null);
                  }}
                  className="text-xs font-bold"
                >
                  Start Over
                </Button>
              </div>
            </div>
          </Card>

          {/* Week-by-Week Timeline Preview */}
          <div className="flex flex-col gap-3">
            <h3 className="text-xs font-extrabold text-text-secondary uppercase tracking-wider px-1">
              Curriculum Preview ({roadmap.weeks?.length || 0} Modules)
            </h3>
            {roadmap.weeks?.map((week) => (
              <Card
                key={week.week}
                className={`transition-all cursor-pointer hover:border-accent/40 ${
                  selectedWeek === week.week ? "border-accent ring-1 ring-accent/20" : ""
                }`}
                onClick={() => setSelectedWeek(selectedWeek === week.week ? null : week.week)}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-xl bg-accent/10 text-accent flex items-center justify-center font-extrabold text-xs border border-accent/20">
                      W{week.week}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-text text-sm">
                        Week {week.week}: {week.topic}
                      </h4>
                      {selectedWeek === week.week ? (
                        <ArrowUp size={14} className="text-text-secondary" />
                      ) : (
                        <ArrowDown size={14} className="text-text-secondary" />
                      )}
                    </div>
                    <p className="text-xs text-text-secondary mt-1 leading-relaxed">{week.goal}</p>

                    {/* Tasks list */}
                    {week.tasks && week.tasks.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/60 space-y-2">
                        <p className="text-[11px] font-bold text-text-secondary uppercase tracking-wider">
                          Key Tasks & Projects:
                        </p>
                        <div className="grid grid-cols-1 gap-1.5">
                          {week.tasks.map((t, idx) => (
                            <div
                              key={idx}
                              className="p-2.5 rounded-xl bg-bg-alt border border-border/80 text-xs space-y-1"
                            >
                              <p className="font-bold text-text flex items-center gap-1.5">
                                <CheckCircle size={12} className="text-accent shrink-0" />
                                <span>{t.title}</span>
                              </p>
                              {t.description && (
                                <p className="text-[11px] text-text-secondary leading-relaxed pl-4">
                                  {t.description}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
