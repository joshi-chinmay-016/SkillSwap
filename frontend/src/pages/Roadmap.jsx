import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import { useToast } from "../components/common/Toast";
import { Sparkles, MapPin, CheckCircle, Circle, Clock, ArrowRight, BookOpen } from "lucide-react";

export default function Roadmap() {
  const { toast } = useToast();
  const [roadmap, setRoadmap] = useState(null);
  const [selectedWeek, setSelectedWeek] = useState(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    defaultValues: {
      target_skill: "",
    },
  });

  const roadmapMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post("/ai/roadmap", data);
      return res.data;
    },
    onSuccess: (data) => {
      setRoadmap(data.roadmap || data);
      toast({ title: "Success", description: "Roadmap generated successfully!" });
    },
    onError: (error) => {
      toast({ 
        title: "Error", 
        description: error.response?.data?.detail || "Failed to generate roadmap",
        variant: "destructive" 
      });
    },
  });

  const onSubmit = (data) => {
    roadmapMutation.mutate(data);
  };

  const mockRoadmap = {
    target_skill: "React Development",
    weeks: [
      {
        week: 1,
        title: "React Fundamentals",
        skills: ["JSX Syntax", "Components & Props", "State Management basics", "Event Handling"],
        completed: false,
      },
      {
        week: 2,
        title: "Hooks Deep Dive",
        skills: ["useState", "useEffect", "useContext", "Custom Hooks"],
        completed: false,
      },
      {
        week: 3,
        title: "React Patterns",
        skills: ["Controlled Components", "Compound Components", "Render Props", "Higher-Order Components"],
        completed: false,
      },
      {
        week: 4,
        title: "State Management",
        skills: ["Redux basics", "Context API patterns", "Zustand", "React Query"],
        completed: false,
      },
      {
        week: 5,
        title: "Routing & Navigation",
        skills: ["React Router v6", "Nested Routes", "Route Guards", "Programmatic Navigation"],
        completed: false,
      },
      {
        week: 6,
        title: "Forms & Validation",
        skills: ["React Hook Form", "Zod validation", "Form handling patterns", "Error handling"],
        completed: false,
      },
      {
        week: 7,
        title: "Performance Optimization",
        skills: ["memo & useMemo", "useCallback", "Code splitting", "Lazy loading"],
        completed: false,
      },
      {
        week: 8,
        title: "Testing",
        skills: ["Jest & RTL", "Component testing", "Integration testing", "E2E with Cypress"],
        completed: false,
      },
    ],
  };

  const displayRoadmap = roadmap || mockRoadmap;

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
      </div>

      {/* Input Form */}
      {!roadmap && (
        <Card title="Generate Your Roadmap" subtitle="Enter a skill you want to learn">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Target Skill"
              placeholder="e.g., React Development, Machine Learning, UX Design"
              icon={<BookOpen size={16} />}
              {...register("target_skill", { required: "Please enter a skill" })}
              error={errors.target_skill?.message}
              disabled={isSubmitting}
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
                <h2 className="text-lg font-bold text-text">{displayRoadmap.target_skill || "Learning Roadmap"}</h2>
                <p className="text-sm text-text-secondary mt-1">
                  {displayRoadmap.weeks?.length || 8} weeks • {displayRoadmap.weeks?.filter(w => w.completed).length || 0} completed
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
                    style={{ width: `${((displayRoadmap.weeks?.filter(w => w.completed).length || 0) / (displayRoadmap.weeks?.length || 8)) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-text-secondary">
                  {Math.round(((displayRoadmap.weeks?.filter(w => w.completed).length || 0) / (displayRoadmap.weeks?.length || 8)) * 100)}%
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
                      <h3 className="font-semibold text-text">Week {week.week}: {week.title}</h3>
                      {selectedWeek === week.week ? (
                        <ArrowUp size={16} className="text-text-secondary" />
                      ) : (
                        <ArrowDown size={16} className="text-text-secondary" />
                      )}
                    </div>
                    <p className="text-sm text-text-secondary mt-1">
                      {week.skills?.length || 4} skills to master
                    </p>
                    
                    {selectedWeek === week.week && (
                      <div className="mt-4 pt-4 border-t border-border">
                        <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
                          Skills & Topics
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {week.skills?.map((skill, skillIndex) => (
                            <div 
                              key={skillIndex}
                              className="flex items-center gap-2 p-2 bg-bg border border-border rounded-lg"
                            >
                              <Circle size={12} className="text-text-secondary" />
                              <span className="text-sm text-text">{skill}</span>
                            </div>
                          ))}
                        </div>
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
