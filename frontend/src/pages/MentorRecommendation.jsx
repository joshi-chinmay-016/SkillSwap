import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import Avatar from "../components/common/Avatar";
import { useToast } from "../components/common/Toast";
import { Sparkles, User, Star, MapPin, BookOpen, ArrowRight, Lightbulb } from "lucide-react";
import CredibilityBadge from "../components/verification/CredibilityBadge";


export default function MentorRecommendation() {
  const toast = useToast();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    defaultValues: {
      target_skill: "",
    },
  });

  const recommendationMutation = useMutation({
    mutationFn: async (data) => {
      // 1. Fetch real peer recommendations from database
      const realRecs = await api.get("/recommendations/me", { params: { limit: 10 } });
      const targetSkillLower = (data.target_skill || "").toLowerCase().trim();

      // Filter or enrich with target skill
      let filtered = realRecs.data.filter((r) =>
        r.matched_skills?.some((s) => s.toLowerCase().includes(targetSkillLower))
      );
      if (filtered.length === 0) {
        filtered = realRecs.data;
      }

      return filtered;
    },
    onSuccess: (data) => {
      setRecommendations(data);
      toast.success("Peer recommendations retrieved!", "Success");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to get recommendations", "Error");
    },
  });


  const onSubmit = (data) => {
    recommendationMutation.mutate(data);
  };


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

      {/* Loading state */}
      {recommendationMutation.isPending && (
        <div className="flex flex-col gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 w-full bg-border/40 animate-pulse rounded-xl" />
          ))}
        </div>
      )}

      {/* Recommendations Display */}
      {recommendations && !recommendationMutation.isPending && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-accent/10 text-accent rounded-lg">
                <Lightbulb size={20} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-text">AI-Recommended Mentors</h2>
                <p className="text-sm text-text-secondary">
                  {recommendations.length} mentors matched to your learning goal
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

          {recommendations.length === 0 ? (
            <Card>
              <div className="py-12 text-center flex flex-col items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-bg-alt flex items-center justify-center text-text-secondary border border-border">
                  <Sparkles size={24} />
                </div>
                <p className="font-semibold text-sm">No mentors available for this skill</p>
                <p className="text-xs text-text-secondary mt-1">
                  No registered mentors were found for your requested skill at this time.
                </p>
                <Button size="sm" variant="outline" onClick={() => navigate("/mentors")} className="mt-2">
                  Browse All Mentors
                </Button>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {recommendations.map((mentor) => (
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
                            {mentor.average_rating != null ? (
                              <div className="flex items-center gap-1">
                                <Star size={14} className="text-warning fill-warning" />
                                <span className="text-sm font-semibold text-text">
                                  {mentor.average_rating.toFixed(1)}
                                </span>
                              </div>
                            ) : null}
                            {mentor.completed_sessions != null ? (
                              <span className="text-xs text-text-secondary">
                                • {mentor.completed_sessions} sessions completed
                              </span>
                            ) : null}
                            <CredibilityBadge
                              status={mentor.verification_status || "CLAIMED"}
                              score={mentor.credibility_score}
                              size="sm"
                            />
                          </div>

                        </div>
                        <Button 
                          variant="primary" 
                          size="sm"
                          onClick={() => {
                            const targetId = mentor.mentor_id || mentor.id;
                            if (targetId) {
                              navigate(`/mentors/${targetId}`, {
                                state: { mentorName: mentor.mentor_name || mentor.name, averageRating: mentor.average_rating }
                              });
                            } else {
                              navigate("/mentors");
                            }
                          }}
                        >
                          <User size={14} className="mr-2" />
                          View Profile & Book
                        </Button>
                      </div>

                      {(mentor.matched_skills?.length > 0 || mentor.expertise?.length > 0) && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {(mentor.matched_skills || mentor.expertise).map((skill, index) => (
                            <span
                              key={index}
                              className="px-2.5 py-1 text-xs font-medium bg-accent/10 text-accent rounded-full border border-accent/10"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}

                      {(mentor.reasons?.length > 0 || mentor.reason) && (
                        <div className="mt-4 p-3 bg-bg-alt border border-border rounded-lg space-y-1.5">
                          <div className="flex items-center gap-2">
                            <Lightbulb size={14} className="text-accent shrink-0" />
                            <p className="text-xs font-bold text-text uppercase tracking-wider">
                              Why this peer mentor?
                            </p>
                          </div>
                          {mentor.reasons ? (
                            mentor.reasons.map((r, rIdx) => (
                              <p key={rIdx} className="text-xs text-text-secondary pl-5">• {r}</p>
                            ))
                          ) : (
                            <p className="text-xs text-text-secondary pl-5">• {mentor.reason}</p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>

              ))}
            </div>
          )}

          <Card className="bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-text">Want more options?</h3>
                <p className="text-sm text-text-secondary mt-1">
                  Browse all available mentors and filter by specific skills
                </p>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => navigate("/mentors")}
              >
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
