import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Avatar from "../components/common/Avatar";
import { useToast } from "../components/common/Toast";
import { Sparkles, User, Star, MapPin, BookOpen, ArrowRight, Lightbulb } from "lucide-react";

export default function MentorRecommendation() {
  const { toast } = useToast();
  const [recommendations, setRecommendations] = useState(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    defaultValues: {
      target_skill: "",
    },
  });

  const recommendationMutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post("/ai/mentor-recommendation", data);
      return res.data;
    },
    onSuccess: (data) => {
      setRecommendations(data.mentors || data);
      toast({ title: "Success", description: "Mentor recommendations generated!" });
    },
    onError: (error) => {
      toast({ 
        title: "Error", 
        description: error.response?.data?.detail || "Failed to get recommendations",
        variant: "destructive" 
      });
    },
  });

  const onSubmit = (data) => {
    recommendationMutation.mutate(data);
  };

  const mockRecommendations = [
    {
      id: 1,
      name: "Sarah Chen",
      avatar_url: null,
      expertise: ["React", "TypeScript", "Node.js"],
      average_rating: 4.8,
      completed_sessions: 42,
      reason: "Sarah has extensive experience in React and has successfully mentored 42 students. Her teaching style focuses on practical, project-based learning which aligns well with your goal of becoming a full-stack developer.",
    },
    {
      id: 2,
      name: "Alex Kumar",
      avatar_url: null,
      expertise: ["JavaScript", "Python", "Data Structures"],
      average_rating: 4.9,
      completed_sessions: 38,
      reason: "Alex specializes in fundamental programming concepts and has a strong background in both frontend and backend development. His systematic approach to teaching algorithms will help you build a solid foundation.",
    },
    {
      id: 3,
      name: "Jordan Lee",
      avatar_url: null,
      expertise: ["React", "Redux", "Testing"],
      average_rating: 4.7,
      completed_sessions: 29,
      reason: "Jordan is an expert in modern React patterns and testing methodologies. If you want to learn industry best practices and write production-ready code, Jordan would be an excellent mentor choice.",
    },
  ];

  const displayRecommendations = recommendations || mockRecommendations;

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">AI Mentor Recommendations</h1>
          <p className="text-sm text-text-secondary mt-1">
            Get personalized mentor suggestions based on your learning goals
          </p>
        </div>
      </div>

      {/* Input Form */}
      {!recommendations && (
        <Card title="Get Personalized Recommendations" subtitle="Tell us what you want to learn">
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
              Get Recommendations
            </Button>
          </form>
        </Card>
      )}

      {/* Recommendations Display */}
      {displayRecommendations && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-accent/10 text-accent rounded-lg">
                <Lightbulb size={20} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-text">AI-Recommended Mentors</h2>
                <p className="text-sm text-text-secondary">
                  {displayRecommendations.length} mentors matched to your learning goal
                </p>
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setRecommendations(null)}
            >
              Search Again
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {displayRecommendations.map((mentor) => (
              <Card key={mentor.id} className="hover:shadow-md transition-shadow">
                <div className="flex flex-col md:flex-row gap-4">
                  <Avatar 
                    src={mentor.avatar_url} 
                    alt={mentor.name} 
                    size="xl" 
                    className="shrink-0"
                  />
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-bold text-text">{mentor.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex items-center gap-1">
                            <Star size={14} className="text-warning fill-warning" />
                            <span className="text-sm font-semibold text-text">
                              {mentor.average_rating?.toFixed(1) || "4.5"}
                            </span>
                          </div>
                          <span className="text-xs text-text-secondary">
                            • {mentor.completed_sessions || 0} sessions completed
                          </span>
                        </div>
                      </div>
                      <Button variant="primary" size="sm">
                        <User size={14} className="mr-2" />
                        View Profile
                      </Button>
                    </div>

                    <div className="flex flex-wrap gap-2 mt-3">
                      {mentor.expertise?.map((skill, index) => (
                        <span
                          key={index}
                          className="px-2.5 py-1 text-xs font-medium bg-accent/10 text-accent rounded-full border border-accent/10"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>

                    <div className="mt-4 p-3 bg-bg-alt border border-border rounded-lg">
                      <div className="flex items-start gap-2">
                        <Lightbulb size={14} className="text-accent shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
                            Why this mentor?
                          </p>
                          <p className="text-sm text-text">{mentor.reason}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <Card className="bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-text">Want more options?</h3>
                <p className="text-sm text-text-secondary mt-1">
                  Browse all available mentors and filter by specific skills
                </p>
              </div>
              <Button variant="outline" size="sm">
                Browse All Mentors
                <ArrowRight size={14} className="ml-2" />
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
