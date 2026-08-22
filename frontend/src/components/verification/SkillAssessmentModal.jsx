import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Modal from "../common/Modal";
import Button from "../common/Button";
import { verificationApi } from "../../api/verificationApi";
import {
  CheckCircle,
  XCircle,
  Award,
  ArrowRight,
  ArrowLeft,
  Clock,
  Zap,
  Flame,
  ShieldAlert,
  RotateCcw,
  Sparkles,
  Check,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { useToast } from "../common/Toast";

export default function SkillAssessmentModal({ isOpen, onClose, skillId, skillName }) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [expandedReviews, setExpandedReviews] = useState({});

  const { data: assessmentData, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["skillAssessment", skillId],
    queryFn: () => verificationApi.getSkillAssessment(skillId),
    enabled: isOpen && !!skillId,
  });

  // Timer effect
  useEffect(() => {
    let interval = null;
    if (isOpen && assessmentData && !assessmentResult) {
      interval = setInterval(() => {
        setSecondsElapsed((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isOpen, assessmentData, assessmentResult]);

  // Keyboard shortcut listener (1-4, A-D, Enter, Arrow keys)
  useEffect(() => {
    if (!isOpen || assessmentResult || !assessmentData?.questions) return;
    const questions = assessmentData.questions;
    const currentQ = questions[currentIndex];

    const handleKeyDown = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

      const key = e.key.toUpperCase();
      let optIdx = -1;

      if (key === "1" || key === "A") optIdx = 0;
      if (key === "2" || key === "B") optIdx = 1;
      if (key === "3" || key === "C") optIdx = 2;
      if (key === "4" || key === "D") optIdx = 3;

      if (optIdx !== -1 && currentQ && optIdx < currentQ.options.length) {
        handleSelectOption(currentQ.id, optIdx);
      }

      if (e.key === "ArrowRight" && currentIndex < questions.length - 1) {
        if (selectedAnswers[currentQ.id] !== undefined) {
          setCurrentIndex((prev) => prev + 1);
        }
      }
      if (e.key === "ArrowLeft" && currentIndex > 0) {
        setCurrentIndex((prev) => prev - 1);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, currentIndex, assessmentData, assessmentResult, selectedAnswers]);

  const submitMutation = useMutation({
    mutationFn: async (answersArray) => {
      return await verificationApi.submitSkillAssessment(skillId, answersArray);
    },
    onSuccess: (data) => {
      setAssessmentResult(data);
      queryClient.invalidateQueries({ queryKey: ["userSkills"] });
      queryClient.invalidateQueries({ queryKey: ["myCredibility"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      if (data.passed) {
        toast.success(`Verified! Score: ${data.score}% (${data.correct_answers}/10 correct)`, "Assessment Passed");
      } else {
        toast.error(`Score: ${data.score}%. Minimum 70% required to pass.`, "Verification Unsuccessful");
      }
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to submit assessment", "Error");
    },
  });

  const handleSelectOption = (questionId, optionIndex) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionIndex,
    }));
  };

  const handleSubmit = () => {
    if (!assessmentData?.questions) return;
    const answersArray = assessmentData.questions.map((q) => ({
      question_id: q.id,
      selected_option: selectedAnswers[q.id] ?? -1,
    }));
    submitMutation.mutate(answersArray);
  };

  const handleResetModal = () => {
    setCurrentIndex(0);
    setSelectedAnswers({});
    setAssessmentResult(null);
    setSecondsElapsed(0);
    setExpandedReviews({});
    onClose();
  };

  const formatTimer = (totalSecs) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const toggleReviewExpand = (idx) => {
    setExpandedReviews((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const questions = assessmentData?.questions || [];
  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;
  const isAnswered = currentQuestion && selectedAnswers[currentQuestion.id] !== undefined;

  const getDifficultyBadge = (difficulty = "") => {
    const diff = difficulty.toUpperCase();
    if (diff === "EASY" || diff === "BEGINNER") {
      return {
        label: "Easy",
        color: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
        icon: Zap,
        glow: "from-emerald-500/10 to-transparent",
      };
    }
    if (diff === "HARD" || diff === "ADVANCED") {
      return {
        label: "Hard",
        color: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20",
        icon: ShieldAlert,
        glow: "from-purple-500/10 to-transparent",
      };
    }
    return {
      label: "Medium",
      color: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
      icon: Flame,
      glow: "from-amber-500/10 to-transparent",
    };
  };

  const currentDiffConfig = currentQuestion ? getDifficultyBadge(currentQuestion.difficulty) : null;
  const DiffIcon = currentDiffConfig?.icon || Zap;

  // Compute breakdown by tier for results view
  const getTierBreakdown = () => {
    if (!assessmentResult || !questions.length) return null;
    const details = assessmentResult.details || [];

    let easyTotal = 0, easyCorrect = 0;
    let medTotal = 0, medCorrect = 0;
    let hardTotal = 0, hardCorrect = 0;

    details.forEach((d, i) => {
      const q = questions[i];
      const diff = (q?.difficulty || "INTERMEDIATE").toUpperCase();
      if (diff === "EASY" || diff === "BEGINNER") {
        easyTotal++;
        if (d.is_correct) easyCorrect++;
      } else if (diff === "HARD" || diff === "ADVANCED") {
        hardTotal++;
        if (d.is_correct) hardCorrect++;
      } else {
        medTotal++;
        if (d.is_correct) medCorrect++;
      }
    });

    return { easyTotal, easyCorrect, medTotal, medCorrect, hardTotal, hardCorrect };
  };

  const tierStats = getTierBreakdown();

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleResetModal}
      title={skillName ? `${skillName} Skill Verification (10 Questions)` : "Skill Verification Assessment"}
      size="xl"
    >
      {isLoading && (
        <div className="py-16 text-center space-y-3">
          <div className="inline-block p-4 rounded-full bg-accent/10 text-accent animate-spin">
            <Sparkles size={32} />
          </div>
          <p className="text-base font-semibold text-text">Generating 10 progressive questions...</p>
          <p className="text-xs text-text-secondary">Preparing Easy → Medium → Hard question progression</p>
        </div>
      )}

      {isError && (
        <div className="py-10 text-center space-y-4">
          <div className="p-4 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 rounded-xl text-sm border border-red-200 dark:border-red-900">
            {error?.response?.data?.detail || "Unable to load questions for this skill."}
          </div>
          <div className="flex justify-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
            <Button variant="primary" size="sm" onClick={handleResetModal}>
              Close
            </Button>
          </div>
        </div>
      )}

      {assessmentData && !assessmentResult && questions.length > 0 && (
        <div className="space-y-6">
          {/* Header Bar with Step Pills & Live Timer */}
          <div className="bg-bg/60 border border-border p-3.5 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${currentDiffConfig.color}`}>
                  <DiffIcon size={13} /> {currentDiffConfig.label} Tier
                </span>
                <span className="text-xs font-medium text-text-secondary hidden sm:inline">
                  Question {currentIndex + 1} of {totalQuestions}
                </span>
              </div>

              <div className="flex items-center gap-4 text-xs font-semibold text-text">
                <div className="flex items-center gap-1.5 bg-bg border border-border px-2.5 py-1 rounded-full text-text-secondary">
                  <Clock size={13} className="text-accent" />
                  <span className="font-mono">{formatTimer(secondsElapsed)}</span>
                </div>
                <span className="text-accent font-bold">Pass: 70%+</span>
              </div>
            </div>

            {/* 10 Step Question Progress Bar */}
            <div className="grid grid-cols-10 gap-1.5 pt-1">
              {questions.map((q, idx) => {
                const isCurrent = idx === currentIndex;
                const isDone = selectedAnswers[q.id] !== undefined;
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => setCurrentIndex(idx)}
                    className={`h-2 rounded-full transition-all cursor-pointer ${
                      isCurrent
                        ? "bg-accent ring-2 ring-accent/40 scale-105"
                        : isDone
                        ? "bg-emerald-500"
                        : "bg-border/60 hover:bg-border"
                    }`}
                    title={`Question ${idx + 1} (${q.difficulty})`}
                  />
                );
              })}
            </div>
          </div>

          {/* Interactive Question Card */}
          {currentQuestion && (
            <div className="bg-bg/30 border border-border p-5 rounded-xl space-y-5 relative overflow-hidden transition-all duration-300">
              <div className="flex items-center justify-between text-xs text-text-secondary">
                <span className="font-mono uppercase tracking-wider font-semibold">
                  Q{currentIndex + 1}. {currentQuestion.difficulty} LEVEL
                </span>
                <span className="text-xs text-text-secondary italic">
                  Press 1-4 or A-D to select
                </span>
              </div>

              <h3 className="text-lg font-bold text-text leading-snug">
                {currentQuestion.question_text}
              </h3>

              {/* 4 Interactive Options */}
              <div className="grid grid-cols-1 gap-3 pt-1">
                {currentQuestion.options.map((optText, optIdx) => {
                  const isSelected = selectedAnswers[currentQuestion.id] === optIdx;
                  return (
                    <button
                      key={optIdx}
                      type="button"
                      onClick={() => handleSelectOption(currentQuestion.id, optIdx)}
                      className={`w-full text-left p-4 rounded-xl border text-sm transition-all flex items-center justify-between gap-3 group cursor-pointer ${
                        isSelected
                          ? "border-accent bg-accent/10 text-accent font-semibold shadow-md ring-1 ring-accent/50"
                          : "border-border hover:border-accent/50 hover:bg-bg/80 text-text"
                      }`}
                    >
                      <div className="flex items-center gap-3.5">
                        <span
                          className={`w-7 h-7 rounded-lg border flex items-center justify-center text-xs font-bold shrink-0 transition-colors ${
                            isSelected
                              ? "border-accent bg-accent text-white"
                              : "border-border bg-bg group-hover:border-accent/40 text-text-secondary"
                          }`}
                        >
                          {String.fromCharCode(65 + optIdx)}
                        </span>
                        <span className="leading-snug">{optText}</span>
                      </div>
                      {isSelected && (
                        <div className="w-5 h-5 rounded-full bg-accent text-white flex items-center justify-center shrink-0 animate-in fade-in zoom-in duration-200">
                          <Check size={12} strokeWidth={3} />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Modal Bottom Controls */}
          <div className="flex justify-between items-center pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentIndex === 0}
            >
              <ArrowLeft size={14} className="mr-1" /> Previous
            </Button>

            <span className="text-xs font-medium text-text-secondary">
              {Object.keys(selectedAnswers).length} of {totalQuestions} answered
            </span>

            {currentIndex < totalQuestions - 1 ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setCurrentIndex((prev) => Math.min(totalQuestions - 1, prev + 1))}
                disabled={!isAnswered}
              >
                Next <ArrowRight size={14} className="ml-1" />
              </Button>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={handleSubmit}
                loading={submitMutation.isPending}
                disabled={Object.keys(selectedAnswers).length < totalQuestions || submitMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
              >
                <Sparkles size={14} className="mr-1.5" /> Complete & Submit
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Visually Stunning Results & Review View */}
      {assessmentResult && (
        <div className="space-y-6 py-1">
          {/* Top Score Banner */}
          <div className="bg-bg/60 border border-border p-6 rounded-2xl text-center space-y-4 relative overflow-hidden">
            <div
              className={`absolute inset-0 opacity-10 bg-gradient-to-b ${
                assessmentResult.passed ? "from-emerald-500 to-transparent" : "from-amber-500 to-transparent"
              }`}
            />
            
            <div className="inline-flex p-4 rounded-full bg-bg border border-border shadow-lg">
              {assessmentResult.passed ? (
                <Award size={48} className="text-emerald-500 animate-bounce" />
              ) : (
                <XCircle size={48} className="text-amber-500" />
              )}
            </div>

            <div>
              <h3 className="text-2xl font-extrabold text-text tracking-tight">
                {assessmentResult.passed ? "Skill Officially Verified!" : "Assessment Completed"}
              </h3>
              <p className="text-sm text-text-secondary mt-1">
                You completed the 10-question evaluation in{" "}
                <span className="font-mono text-text font-semibold">{formatTimer(secondsElapsed)}</span>.
              </p>
            </div>

            {/* Score Ring / Pill */}
            <div className="flex justify-center items-center gap-4 pt-1">
              <div className="px-5 py-2.5 rounded-2xl bg-bg border border-border shadow-xs text-center">
                <span className="text-xs uppercase font-bold text-text-secondary tracking-wider block">Final Score</span>
                <span className={`text-3xl font-black ${assessmentResult.passed ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600"}`}>
                  {assessmentResult.score}%
                </span>
              </div>

              <div className="px-5 py-2.5 rounded-2xl bg-bg border border-border shadow-xs text-center">
                <span className="text-xs uppercase font-bold text-text-secondary tracking-wider block">Correct</span>
                <span className="text-3xl font-black text-text">
                  {assessmentResult.correct_answers} / 10
                </span>
              </div>

              <div className="px-5 py-2.5 rounded-2xl bg-bg border border-border shadow-xs text-center">
                <span className="text-xs uppercase font-bold text-text-secondary tracking-wider block">Status</span>
                <span className="text-base font-extrabold text-accent mt-1 block">
                  {assessmentResult.new_verification_status}
                </span>
              </div>
            </div>
          </div>

          {/* Difficulty Tier Stats Breakdown */}
          {tierStats && (
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 block uppercase">⚡ Easy Tier</span>
                <span className="text-lg font-extrabold text-text mt-0.5 block">
                  {tierStats.easyCorrect} / {tierStats.easyTotal}
                </span>
              </div>
              <div className="p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl">
                <span className="text-xs font-bold text-amber-600 dark:text-amber-400 block uppercase">🔥 Medium Tier</span>
                <span className="text-lg font-extrabold text-text mt-0.5 block">
                  {tierStats.medCorrect} / {tierStats.medTotal}
                </span>
              </div>
              <div className="p-3 bg-purple-500/5 border border-purple-500/20 rounded-xl">
                <span className="text-xs font-bold text-purple-600 dark:text-purple-400 block uppercase">🚀 Hard Tier</span>
                <span className="text-lg font-extrabold text-text mt-0.5 block">
                  {tierStats.hardCorrect} / {tierStats.hardTotal}
                </span>
              </div>
            </div>
          )}

          {/* Question-by-Question Detailed Review */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
              10-Question Comprehensive Review
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {assessmentResult.details.map((detail, idx) => {
                const isExpanded = expandedReviews[idx];
                const q = questions[idx];
                return (
                  <div
                    key={idx}
                    className={`rounded-xl border transition-all ${
                      detail.is_correct
                        ? "bg-emerald-500/5 border-emerald-500/20"
                        : "bg-red-500/5 border-red-500/20"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => toggleReviewExpand(idx)}
                      className="w-full p-3 flex items-center justify-between text-left text-xs font-semibold cursor-pointer"
                    >
                      <div className="flex items-center gap-2.5">
                        {detail.is_correct ? (
                          <CheckCircle size={16} className="text-emerald-500 shrink-0" />
                        ) : (
                          <XCircle size={16} className="text-red-500 shrink-0" />
                        )}
                        <span className="text-text font-medium line-clamp-1">
                          Q{idx + 1} ({q?.difficulty || "MEDIUM"}): {q?.question_text || "Question"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={detail.is_correct ? "text-emerald-600 dark:text-emerald-400 font-bold" : "text-red-600 font-bold"}>
                          {detail.is_correct ? "+10%" : "0%"}
                        </span>
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-3 pb-3 text-xs space-y-1.5 border-t border-border/40 pt-2 text-text-secondary">
                        {q?.options && (
                          <p>
                            <strong className="text-text">Your Answer:</strong>{" "}
                            {detail.selected_option >= 0 ? q.options[detail.selected_option] : "Not answered"}
                          </p>
                        )}
                        {!detail.is_correct && q?.options && (
                          <p className="text-emerald-600 dark:text-emerald-400 font-semibold">
                            <strong>Correct Answer:</strong> {q.options[detail.correct_option]}
                          </p>
                        )}
                        {detail.explanation && (
                          <p className="italic bg-bg/50 p-2 rounded border border-border/50 text-text mt-1">
                            💡 {detail.explanation}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setAssessmentResult(null);
                setCurrentIndex(0);
                setSelectedAnswers({});
                setSecondsElapsed(0);
              }}
            >
              <RotateCcw size={14} className="mr-1.5" /> Retake Assessment
            </Button>
            <Button variant="primary" size="sm" onClick={handleResetModal}>
              Done
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
