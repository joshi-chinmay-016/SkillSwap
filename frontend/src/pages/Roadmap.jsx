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
import { Sparkles, MapPin, CheckCircle, Circle, Clock, ArrowRight, BookOpen, Target, ArrowUp, ArrowDown, Compass } from "lucide-react";

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

  const { control, register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    defaultValues: {
      target_role: "",
      experience_level: "beginner",
      duration_months: "3",
    },
  });

  const roadmapMutation = useMutation({
    mutationFn: async (data) => {
      console.log("Sending roadmap request:", data);
      const res = await api.post("/ai/roadmap", data);
      console.log("Roadmap response:", res.data);
      return res.data;
    },
    onSuccess: (data) => {
      console.log("Roadmap success:", data);
      setRoadmap(data);
      toast.success("Roadmap generated successfully!", "Success");
    },
    onError: (error) => {
      console.error("Roadmap error:", error);
      toast.error(error.response?.data?.detail || "Failed to generate roadmap", "Error");
    },
  });

  const validateRoadmap = (rm) => {
    if (!rm || !rm.title || !Array.isArray(rm.weeks) || rm.weeks.length === 0) return false;
    return rm.weeks.every(w => 
      typeof w.week === 'number' && 
      typeof w.topic === 'string' && w.topic.trim().length > 0 &&
      typeof w.goal === 'string' && w.goal.trim().length > 0
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
        weeks: roadmap.weeks.map(w => ({
          week: w.week,
          topic: w.topic,
          goal: w.goal,
          tasks: w.tasks?.map(t => ({ title: t.title, description: t.description, resources: t.resources }))
        }))
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
      toast.error(error.response?.data?.detail || "Failed to save learning journey", "Error");
    }
  });

  const handleSaveJourney = () => {
    if (!validateRoadmap(roadmap)) {
      toast.error("The generated roadmap is malformed. Please regenerate a new one.", "Invalid Roadmap");
      return;
    }
    saveJourneyMutation.mutate();
  };

  const onSubmit = (data) => {
    const currentSkillsList = userSkills.map(s => s.skill?.name || s.name).filter(name => name);
    if (currentSkillsList.length === 0) {
      toast.error("Please add at least one skill to your profile first", "Error");
      return;
    }
    const payload = {
      current_skills: currentSkillsList,
      target_role: data.target_role,
      experience_level: data.experience_level,
      duration_months: parseInt(data.duration_months, 10),
    };
    setRoadmapRequestSnapshot(payload);
    roadmapMutation.mutate(payload);
  };

  if (isLoadingActive && !isForceNew) {
    return (
      <div className="flex flex-col gap-4">
        <div className="h-12 w-48 bg-border/40 animate-pulse rounded-lg" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 w-full bg-border/40 animate-pulse rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">AI Roadmap Builder</h1>
          <p className="text-sm text-text-secondary mt-1">
            Generate a personalized learning plan for any skill
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => navigate("/journey/skill-gap")}
        >
          <Target size={16} className="mr-2" />
          Analyze Skill Gap
        </Button>
      </div>

      {/* Empty State when no active journey and no roadmap exists */}
      {!roadmap && !roadmapMutation.isPending && !showForm && (
        <Card className="text-center py-12 flex flex-col items-center justify-center border-dashed border-2 border-border max-w-2xl mx-auto w-full">
          <div className="p-4 bg-accent/10 text-accent rounded-full mb-4">
            <Compass size={36} className="animate-pulse" />
          </div>
          <h2 className="text-lg font-bold tracking-tight text-text">Your learning journey starts here</h2>
          <p className="text-sm text-text-secondary mt-2 max-w-md">
            Generate a personalized AI roadmap based on your current skills, experience, and career goal. Save it as a journey to begin tracking real progress.
          </p>
          <div className="mt-6 flex gap-3">
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowForm(true)}
            >
              <Sparkles size={16} className="mr-2" />
              Generate AI Roadmap
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/profile")}
            >
              Explore Skills
            </Button>
          </div>
        </Card>
      )}

      {/* Input Form */}
      {!roadmap && !roadmapMutation.isPending && showForm && (
        <Card title="Generate Your Roadmap" subtitle="Enter your learning goals" className="!overflow-visible">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text mb-2">Current Skills</label>
              <div className="flex flex-wrap gap-2 mb-2">
                  {userSkills.length === 0 ? (
                    <p className="text-xs text-text-secondary italic">No skills in your profile yet. Add skills in Profile settings.</p>
                  ) : (
                    userSkills.map((skill) => (
                      <div key={skill.id} className="px-3 py-1.5 bg-bg-alt border border-border rounded-md text-sm text-text">
                        {skill.skill?.name || skill.name}
                      </div>
                    ))
                  )}
              </div>
              <p className="text-xs text-text-secondary">Your current skills will be used to personalize the roadmap</p>
            </div>

            <Input
              label="Target Role"
              placeholder="e.g., React Developer, Data Scientist, UX Designer"
              icon={<BookOpen size={16} />}
              {...register("target_role", { required: "Please enter a target role" })}
              error={errors.target_role?.message}
              disabled={isSubmitting}
            />

            <Controller
              name="experience_level"
              control={control}
              rules={{ required: "Please select experience level" }}
              render={({ field }) => (
                <Select
                  label="Experience Level"
                  options={[
                    { value: "beginner", label: "Beginner" },
                    { value: "intermediate", label: "Intermediate" },
                    { value: "advanced", label: "Advanced" },
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
                  label="Duration (months)"
                  options={[
                    { value: "1", label: "1 month" },
                    { value: "3", label: "3 months" },
                    { value: "6", label: "6 months" },
                    { value: "12", label: "12 months" },
                    { value: "18", label: "18 months" },
                    { value: "24", label: "24 months" },
                  ]}
                  value={field.value}
                  onChange={field.onChange}
                  error={errors.duration_months?.message}
                  disabled={isSubmitting}
                />
              )}
            />

            <div className="flex gap-3 pt-2">
              <Button 
                type="submit" 
                variant="primary" 
                size="sm"
                disabled={isSubmitting}
                loading={isSubmitting}
                className="flex-1"
              >
                <Sparkles size={16} className="mr-2" />
                Generate Roadmap
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() => setShowForm(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Loading state */}
      {roadmapMutation.isPending && (
        <div className="flex flex-col gap-4">
          <div className="h-10 w-1/3 bg-border/40 animate-pulse rounded-lg" />
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 w-full bg-border/40 animate-pulse rounded-xl" />
          ))}
        </div>
      )}

      {/* Roadmap Display */}
      {roadmap && !roadmapMutation.isPending && (
        <>
          {/* Review & Save Summary Card */}
          <Card className="bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-xs font-semibold text-accent uppercase tracking-wider">AI Generated Roadmap</span>
                <h2 className="text-lg font-bold text-text mt-0.5">{roadmap.title || "Learning Roadmap"}</h2>
                <p className="text-xs text-text-secondary mt-1">
                  {roadmap.weeks?.length || 0} weeks • Ready to be saved to your learning journeys
                </p>
              </div>
              <div className="flex items-center gap-2 self-start sm:self-auto">
                <Button 
                  variant="primary" 
                  size="sm"
                  onClick={handleSaveJourney}
                  disabled={saveJourneyMutation.isPending}
                  loading={saveJourneyMutation.isPending}
                >
                  <Sparkles size={16} className="mr-2" />
                  {saveJourneyMutation.isPending ? "Saving Journey..." : "Save as Learning Journey"}
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
                >
                  Cancel
                </Button>
              </div>
            </div>
          </Card>

          {/* Week-by-Week Timeline Preview */}
          <div className="flex flex-col gap-4">
            <h3 className="text-sm font-semibold text-text-secondary px-1">Roadmap Preview</h3>
            {roadmap.weeks?.map((week) => (
              <Card 
                key={week.week}
                className={`transition-all hover:shadow-sm ${selectedWeek === week.week ? 'border-accent/40 ring-1 ring-accent/10' : ''}`}
                onClick={() => setSelectedWeek(selectedWeek === week.week ? null : week.week)}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-accent/10 text-accent flex items-center justify-center font-bold text-sm">
                      {week.week}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-text text-sm">Week {week.week}: {week.topic}</h4>
                      {selectedWeek === week.week ? (
                        <ArrowUp size={14} className="text-text-secondary" />
                      ) : (
                        <ArrowDown size={14} className="text-text-secondary" />
                      )}
                    </div>
                    <p className="text-xs text-text-secondary mt-1">
                      {week.goal}
                    </p>
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
