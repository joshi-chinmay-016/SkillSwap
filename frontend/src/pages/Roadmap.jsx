import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Controller } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Select from "../components/common/Select";
import { useToast } from "../components/common/Toast";
import { Sparkles, MapPin, CheckCircle, Circle, Clock, ArrowRight, BookOpen, Target } from "lucide-react";

export default function Roadmap() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [roadmap, setRoadmap] = useState(null);
  const [selectedWeek, setSelectedWeek] = useState(null);

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

  const onSubmit = (data) => {
    // Convert duration_months to number for backend
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
    roadmapMutation.mutate(payload);
  };

  const displayRoadmap = roadmap;

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

      {/* Input Form */}
      {!roadmap && (
        <Card title="Generate Your Roadmap" subtitle="Enter your learning goals">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text mb-2">Current Skills</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {userSkills.map((skill) => (
                  <div key={skill.id} className="px-3 py-1.5 bg-bg-alt border border-border rounded-md text-sm text-text">
                    {skill.name}
                  </div>
                ))}
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

            <Button 
              type="submit" 
              variant="primary" 
              size="sm"
              disabled={isSubmitting}
              loading={isSubmitting}
              className="w-full"
            >
              <Sparkles size={16} className="mr-2" />
              Generate Roadmap
            </Button>
          </form>
        </Card>
      )}

      {/* Roadmap Display */}
      {displayRoadmap && (
        <>
          {/* Progress Overview */}
          <Card className="bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-text">{displayRoadmap.title || "Learning Roadmap"}</h2>
                <p className="text-sm text-text-secondary mt-1">
                  {displayRoadmap.weeks?.length || 0} weeks • {displayRoadmap.weeks?.filter(w => w.completed).length || 0} completed
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    setRoadmap(null);
                    setSelectedWeek(null);
                  }}
                >
                  Generate New
                </Button>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-accent transition-all duration-500"
                    style={{ width: `${((displayRoadmap.weeks?.filter(w => w.completed).length || 0) / (displayRoadmap.weeks?.length || 1)) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-text-secondary">
                  {Math.round(((displayRoadmap.weeks?.filter(w => w.completed).length || 0) / (displayRoadmap.weeks?.length || 1)) * 100)}%
                </span>
              </div>
            </div>
          </Card>

          {/* Week-by-Week Timeline */}
          <div className="flex flex-col gap-4">
            {displayRoadmap.weeks?.map((week, index) => (
              <Card 
                key={week.week}
                className={`cursor-pointer transition-all hover:shadow-md ${selectedWeek === week.week ? 'border-accent ring-2 ring-accent/20' : ''}`}
                onClick={() => setSelectedWeek(selectedWeek === week.week ? null : week.week)}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    {week.completed ? (
                      <div className="w-10 h-10 rounded-full bg-success/10 text-success flex items-center justify-center">
                        <CheckCircle size={20} />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-accent/10 text-accent flex items-center justify-center font-bold">
                        {week.week}
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-text">Week {week.week}: {week.topic}</h3>
                      {selectedWeek === week.week ? (
                        <ArrowUp size={16} className="text-text-secondary" />
                      ) : (
                        <ArrowDown size={16} className="text-text-secondary" />
                      )}
                    </div>
                    <p className="text-sm text-text-secondary mt-1">
                      {week.goal}
                    </p>
                    
                    {selectedWeek === week.week && (
                      <div className="mt-4 pt-4 border-t border-border">
                        <div className="mt-4 flex gap-2">
                          <Button variant="primary" size="sm">
                            <CheckCircle size={14} className="mr-2" />
                            Mark as Complete
                          </Button>
                          <Button variant="outline" size="sm">
                            <Clock size={14} className="mr-2" />
                            Schedule Session
                          </Button>
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
