import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Textarea from "../components/common/Textarea";
import { useToast } from "../components/common/Toast";
import { BookOpen, AlertTriangle, CheckCircle, XCircle, TrendingUp, Target, Sparkles } from "lucide-react";

export default function SkillGap() {
  const { toast } = useToast();
  const [analysis, setAnalysis] = useState(null);

  const { data: userSkills = [] } = useQuery({
    queryKey: ["userSkills"],
    queryFn: async () => {
      const res = await api.get("/skills/me");
      return res.data;
    },
  });

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    defaultValues: {
      target_role: "",
      current_skills: "",
    },
  });

  const skillGapMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post("/ai/skill-gap", data);
      return res.data;
    },
    onSuccess: (data) => {
      setAnalysis(data);
      toast({ title: "Success", description: "Skill gap analysis completed!" });
    },
    onError: (error) => {
      toast({ 
        title: "Error", 
        description: error.response?.data?.detail || "Failed to analyze skill gap",
        variant: "destructive" 
      });
    },
  });

  const onSubmit = (data) => {
    skillGapMutation.mutate(data);
  };

  const mockAnalysis = {
    target_role: "Full Stack Developer",
    current_skills: ["JavaScript", "HTML", "CSS"],
    gap: [
      { skill: "React.js", importance: "high", status: "missing" },
      { skill: "Node.js", importance: "high", status: "missing" },
      { skill: "TypeScript", importance: "medium", status: "missing" },
      { skill: "Database Design", importance: "high", status: "missing" },
      { skill: "API Development", importance: "high", status: "missing" },
      { skill: "Git & Version Control", importance: "medium", status: "covered" },
      { skill: "Testing", importance: "medium", status: "missing" },
      { skill: "Cloud Deployment", importance: "low", status: "missing" },
    ],
    suggestions: [
      "Start with React fundamentals and build small projects",
      "Learn Node.js and Express for backend development",
      "Practice building REST APIs",
      "Study database concepts (SQL and NoSQL)",
      "Learn TypeScript for better type safety",
    ],
  };

  const displayAnalysis = analysis || mockAnalysis;

  const learnSkills = userSkills.filter((s) => s.type === "learn").map((s) => s.skill?.name || s.name);

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Skill Gap Analyzer</h1>
          <p className="text-sm text-text-secondary mt-1">
            Identify missing skills for your target role
          </p>
        </div>
      </div>

      {/* Input Form */}
      {!analysis && (
        <Card title="Analyze Your Skill Gap" subtitle="Compare your current skills with your target role">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Target Role"
              placeholder="e.g., Full Stack Developer, Data Scientist, UX Designer"
              icon={<Target size={16} />}
              {...register("target_role", { required: "Please enter a target role" })}
              error={errors.target_role?.message}
              disabled={isSubmitting}
            />

            <Textarea
              label="Current Skills"
              placeholder="List your current skills (comma-separated)"
              rows={3}
              defaultValue={learnSkills.join(", ")}
              {...register("current_skills")}
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
              Analyze Skill Gap
            </Button>
          </form>
        </Card>
      )}

      {/* Analysis Results */}
      {displayAnalysis && (
        <>
          {/* Summary Card */}
          <Card className="bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-accent/10 text-accent rounded-xl">
                  <TrendingUp size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-text">Target: {displayAnalysis.target_role}</h2>
                  <p className="text-sm text-text-secondary mt-1">
                    {displayAnalysis.gap?.filter(g => g.status === "missing").length || 5} skills to learn • 
                    {displayAnalysis.gap?.filter(g => g.status === "covered").length || 1} already mastered
                  </p>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setAnalysis(null)}
              >
                Analyze New Role
              </Button>
            </div>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Missing Skills */}
            <Card title="Missing Skills" subtitle="Skills you need to acquire">
              <div className="space-y-2">
                {displayAnalysis.gap?.filter(g => g.status === "missing").map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-bg border border-border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 bg-danger/10 text-danger rounded">
                        <XCircle size={14} />
                      </div>
                      <span className="text-sm font-medium text-text">{item.skill}</span>
                    </div>
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                      item.importance === "high" 
                        ? "bg-danger/10 text-danger" 
                        : item.importance === "medium"
                        ? "bg-warning/10 text-warning"
                        : "bg-bg-alt text-text-secondary"
                    }`}>
                      {item.importance}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Covered Skills */}
            <Card title="Skills You Have" subtitle="Already mastered for this role">
              <div className="space-y-2">
                {displayAnalysis.gap?.filter(g => g.status === "covered").map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-bg border border-border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 bg-success/10 text-success rounded">
                        <CheckCircle size={14} />
                      </div>
                      <span className="text-sm font-medium text-text">{item.skill}</span>
                    </div>
                    <span className="text-xs font-semibold text-success">Covered</span>
                  </div>
                ))}
                {displayAnalysis.gap?.filter(g => g.status === "covered").length === 0 && (
                  <div className="py-8 text-center">
                    <AlertTriangle size={24} className="text-text-secondary mx-auto mb-2" />
                    <p className="text-sm text-text-secondary">No skills match this role yet</p>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* AI Suggestions */}
          <Card title="AI Recommendations" subtitle="Personalized learning path suggestions">
            <div className="space-y-3">
              {displayAnalysis.suggestions?.map((suggestion, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-bg border border-border rounded-lg"
                >
                  <div className="p-1.5 bg-accent/10 text-accent rounded mt-0.5">
                    <BookOpen size={14} />
                  </div>
                  <p className="text-sm text-text">{suggestion}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-border">
              <Button variant="primary" size="sm" className="w-full">
                <Target size={16} className="mr-2" />
                Generate Learning Roadmap
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
