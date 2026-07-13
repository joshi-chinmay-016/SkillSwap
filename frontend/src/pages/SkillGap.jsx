import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Textarea from "../components/common/Textarea";
import { useToast } from "../components/common/Toast";
import { BookOpen, AlertTriangle, CheckCircle, XCircle, TrendingUp, Target, Sparkles } from "lucide-react";
import SkillGapLoadingScreen from "../components/skill-gap/SkillGapLoadingScreen";

export default function SkillGap() {
  const toast = useToast();
  const navigate = useNavigate();
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
      console.log("Sending skill gap request:", data);
      const res = await api.post("/ai/skill-gap", data);
      console.log("Skill gap response:", res.data);
      return res.data;
    },
    onSuccess: (data) => {
      console.log("Skill gap success:", data);
      setAnalysis(data);
      toast.success("Skill gap analysis completed!", "Success");
    },
    onError: (error) => {
      console.error("Skill gap error:", error);
      toast.error(error.response?.data?.detail || "Failed to analyze skill gap", "Error");
    },
  });

  const onSubmit = (data) => {
    // Parse current_skills from comma-separated string to array
    const payload = {
      target_role: data.target_role,
      current_skills: data.current_skills
        .split(",")
        .map(s => s.trim())
        .filter(s => s.length > 0),
    };
    skillGapMutation.mutate(payload);
  };


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
      {!analysis && !skillGapMutation.isPending && (
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

      {/* Loading state */}
      {skillGapMutation.isPending && (
        <SkillGapLoadingScreen isOpen={true} onCancel={() => skillGapMutation.reset()} />
      )}

      {/* Analysis Results */}
      {analysis && (
        <>
          {/* Summary Card */}
          <Card className="bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-accent/10 text-accent rounded-xl">
                  <TrendingUp size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-text">Target: {analysis.target_role}</h2>
                  <p className="text-sm text-text-secondary mt-1">
                    {analysis.missing_skills?.length || 0} skills to learn • 
                    {analysis.matched_skills?.length || 0} already mastered
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
                {analysis.missing_skills?.map((skill, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-bg border border-border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 bg-danger/10 text-danger rounded">
                        <XCircle size={14} />
                      </div>
                      <span className="text-sm font-medium text-text">{skill}</span>
                    </div>
                    <span className="text-xs font-semibold px-2 py-1 rounded-full bg-danger/10 text-danger">
                      Missing
                    </span>
                  </div>
                ))}
                {(!analysis.missing_skills || analysis.missing_skills.length === 0) && (
                  <div className="py-8 text-center">
                    <CheckCircle size={24} className="text-success mx-auto mb-2" />
                    <p className="text-sm text-text-secondary">You have all the skills for this role!</p>
                  </div>
                )}
              </div>
            </Card>

            {/* Covered Skills */}
            <Card title="Skills You Have" subtitle="Already mastered for this role">
              <div className="space-y-2">
                {analysis.matched_skills?.map((skill, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-bg border border-border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 bg-success/10 text-success rounded">
                        <CheckCircle size={14} />
                      </div>
                      <span className="text-sm font-medium text-text">{skill}</span>
                    </div>
                    <span className="text-xs font-semibold text-success">Covered</span>
                  </div>
                ))}
                {(!analysis.matched_skills || analysis.matched_skills.length === 0) && (
                  <div className="py-8 text-center">
                    <AlertTriangle size={24} className="text-text-secondary mx-auto mb-2" />
                    <p className="text-sm text-text-secondary">No skills match this role yet</p>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* AI Recommendations */}
          <Card title="AI Recommendations" subtitle="Personalized learning path suggestions">
            <div className="space-y-3">
              {analysis.recommendations?.map((recommendation, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-bg border border-border rounded-lg"
                >
                  <div className="p-1.5 bg-accent/10 text-accent rounded mt-0.5">
                    <BookOpen size={14} />
                  </div>
                  <p className="text-sm text-text">{recommendation}</p>
                </div>
              ))}
              {(!analysis.recommendations || analysis.recommendations.length === 0) && (
                <div className="py-8 text-center">
                  <p className="text-sm text-text-secondary">No recommendations available</p>
                </div>
              )}
            </div>
            <div className="mt-4 pt-4 border-t border-border">
              <Button 
                variant="primary" 
                size="sm" 
                className="w-full"
                onClick={() => navigate("/journey/roadmap")}
              >
                <Sparkles size={16} className="mr-2" />
                Generate Learning Roadmap
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
