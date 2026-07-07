import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import api from "../services/api";
import { useAuthStore } from "../store/authStore";
import Card from "../components/common/Card";
import Input from "../components/common/Input";
import Textarea from "../components/common/Textarea";
import Button from "../components/common/Button";

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [bio, setBio] = useState("");
  const [department, setDepartment] = useState("");
  const [year, setYear] = useState("");
  const [availableSkills, setAvailableSkills] = useState([]);
  const [selectedTeach, setSelectedTeach] = useState([]);
  const [selectedLearn, setSelectedLearn] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingSkills, setIsLoadingSkills] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [newTeachSkill, setNewTeachSkill] = useState("");
  const [newLearnSkill, setNewLearnSkill] = useState("");
  const [isCreatingSkill, setIsCreatingSkill] = useState(false);

  const user = useAuthStore((state) => state.user);
  const updateUserStore = useAuthStore((state) => state.updateUser);
  const navigate = useNavigate();

  // Fetch all available skills from backend
  useEffect(() => {
    const fetchSkills = async () => {
      setIsLoadingSkills(true);
      try {
        const response = await api.get("/skills");
        // If there are no skills in backend, populate with some default ones for UX
        if (response.data.length === 0) {
          const defaultSkills = [
            { id: 1, name: "Python", category: "Programming" },
            { id: 2, name: "React", category: "Web Development" },
            { id: 3, name: "Data Structures & Algorithms", category: "Computer Science" },
            { id: 4, name: "Machine Learning", category: "AI" },
            { id: 5, name: "SQL & Databases", category: "Data Science" },
            { id: 6, name: "UI/UX Design", category: "Design" },
            { id: 7, name: "Product Management", category: "Business" },
            { id: 8, name: "Public Speaking", category: "Soft Skills" },
          ];
          
          // Seed the backend with default skills if empty
          const seedPromises = defaultSkills.map(s => 
            api.post("/skills", { name: s.name, category: s.category, description: `${s.name} skill` })
          );
          await Promise.all(seedPromises);
          
          // Refetch from backend
          const refetchResponse = await api.get("/skills");
          setAvailableSkills(refetchResponse.data);
        } else {
          setAvailableSkills(response.data);
        }
      } catch (err) {
        console.error("Failed to load skills:", err);
        // Fallback local list if API fails entirely
        setAvailableSkills([
          { id: 1, name: "Python", category: "Programming" },
          { id: 2, name: "React", category: "Web Development" },
          { id: 3, name: "Algorithms", category: "Computer Science" },
          { id: 4, name: "UI/UX Design", category: "Design" }
        ]);
      } finally {
        setIsLoadingSkills(false);
      }
    };
    fetchSkills();
  }, []);

  const handleNext = () => {
    if (step === 1 && (!bio || !department || !year)) {
      setErrorMessage("Please fill in all fields before moving on.");
      return;
    }
    setErrorMessage("");
    setStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setErrorMessage("");
    setStep((prev) => prev - 1);
  };

  const toggleSkill = (skillId, listType) => {
    if (listType === "teach") {
      setSelectedTeach((prev) =>
        prev.includes(skillId)
          ? prev.filter((id) => id !== skillId)
          : [...prev, skillId]
      );
    } else {
      setSelectedLearn((prev) =>
        prev.includes(skillId)
          ? prev.filter((id) => id !== skillId)
          : [...prev, skillId]
      );
    }
  };

  const handleCreateSkill = async (skillName, listType) => {
    if (!skillName.trim()) return;
    
    setIsCreatingSkill(true);
    try {
      const res = await api.post("/skills", {
        name: skillName.trim(),
        category: "general",
        description: `${skillName} skill`,
      });
      
      const newSkill = res.data;
      setAvailableSkills((prev) => [...prev, newSkill]);
      
      if (listType === "teach") {
        setSelectedTeach((prev) => [...prev, newSkill.id]);
        setNewTeachSkill("");
      } else {
        setSelectedLearn((prev) => [...prev, newSkill.id]);
        setNewLearnSkill("");
      }
    } catch (err) {
      console.error("Failed to create skill:", err);
      setErrorMessage("Failed to create skill. Please try again.");
    } finally {
      setIsCreatingSkill(false);
    }
  };

  const handleFinish = async () => {
    setIsSubmitting(true);
    setErrorMessage("");
    try {
      // 1. Update Profile (bio, department, year)
      await api.put("/profiles/me", {
        bio,
        department,
        year: parseInt(year) || 1,
        avatar_url: `https://api.dicebear.com/7.x/adventurer/svg?seed=${user?.name || "SkillSwap"}`,
      });

      // 2. Assign Teach Skills
      const teachPromises = selectedTeach.map((skillId) =>
        api.post("/skills/me", {
          skill_id: skillId,
          type: "teach",
        })
      );

      // 3. Assign Learn Skills
      const learnPromises = selectedLearn.map((skillId) =>
        api.post("/skills/me", {
          skill_id: skillId,
          type: "learn",
        })
      );

      await Promise.all([...teachPromises, ...learnPromises]);

      // 4. Update local user store and redirect to dashboard
      updateUserStore({ onboardingCompleted: true });
      navigate("/dashboard");
    } catch (err) {
      console.error("Onboarding failed:", err);
      setErrorMessage("Onboarding failed to save. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const progressPct = (step / 4) * 100;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg px-4 select-none">
      <div className="w-full max-w-xl">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center text-xs font-semibold text-text-secondary mb-2">
            <span>STEP {step} OF 4</span>
            <span>{Math.round(progressPct)}% COMPLETE</span>
          </div>
          <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-accent"
              initial={{ width: 0 }}
              animate={{ width: `${progressPct}%` }}
              transition={{ duration: 0.2 }}
            />
          </div>
        </div>

        {errorMessage && (
          <div className="mb-4 p-3 text-xs bg-danger/10 border border-danger/20 text-danger rounded-md font-medium text-left">
            {errorMessage}
          </div>
        )}

        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <Card title="Tell us about yourself" subtitle="Step 1: Profile Details">
                <div className="flex flex-col gap-4">
                  <Textarea
                    label="Short Bio"
                    placeholder="Tell other students what you're passionate about, your hobbies, or what you study..."
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    rows={4}
                  />

                  <Input
                    label="Department / Major"
                    placeholder="Computer Science, Physics, Business..."
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                  />

                  <Input
                    label="Academic Year"
                    type="number"
                    placeholder="1, 2, 3, 4..."
                    min="1"
                    max="6"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                  />

                  <div className="flex justify-end mt-4">
                    <Button onClick={handleNext}>Continue</Button>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <Card
                title="What skills can you teach?"
                subtitle="Step 2: Offer Expertise. Select all that apply."
              >
                {isLoadingSkills ? (
                  <div className="py-12 flex justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
                  </div>
                ) : (
                  <>
                    <div className="flex flex-wrap gap-2.5 max-h-[300px] overflow-y-auto p-1">
                      {availableSkills.map((skill) => {
                        const isSelected = selectedTeach.includes(skill.id);
                        return (
                          <button
                            key={skill.id}
                            type="button"
                            onClick={() => toggleSkill(skill.id, "teach")}
                            className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all cursor-pointer ${
                              isSelected
                                ? "bg-accent text-white border-accent shadow-sm scale-102"
                                : "bg-bg text-text border-border hover:border-accent/40"
                            }`}
                          >
                            {skill.name}
                            <span className="ml-1.5 opacity-60 text-[10px]">
                              ({skill.category})
                            </span>
                          </button>
                        );
                      })}
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-border">
                      <label className="block text-xs font-medium text-text-secondary mb-2">
                        Or create a new skill to teach
                      </label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Enter skill name..."
                          value={newTeachSkill}
                          onChange={(e) => setNewTeachSkill(e.target.value)}
                          disabled={isCreatingSkill}
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCreateSkill(newTeachSkill, "teach")}
                          disabled={!newTeachSkill.trim() || isCreatingSkill}
                          loading={isCreatingSkill}
                        >
                          Add
                        </Button>
                      </div>
                    </div>
                  </>
                )}
                <div className="flex justify-between mt-6">
                  <Button variant="outline" onClick={handleBack}>
                    Back
                  </Button>
                  <Button onClick={handleNext}>Continue</Button>
                </div>
              </Card>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <Card
                title="What skills do you want to learn?"
                subtitle="Step 3: Gain Knowledge. Select all that apply."
              >
                {isLoadingSkills ? (
                  <div className="py-12 flex justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
                  </div>
                ) : (
                  <>
                    <div className="flex flex-wrap gap-2.5 max-h-[300px] overflow-y-auto p-1">
                      {availableSkills.map((skill) => {
                        const isSelected = selectedLearn.includes(skill.id);
                        const isTeaching = selectedTeach.includes(skill.id);
                        return (
                          <button
                            key={skill.id}
                            type="button"
                            disabled={isTeaching}
                            onClick={() => toggleSkill(skill.id, "learn")}
                            className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all cursor-pointer ${
                              isSelected
                                ? "bg-accent text-white border-accent shadow-sm scale-102"
                                : "bg-bg text-text border-border hover:border-accent/40"
                            } ${isTeaching ? "opacity-30 cursor-not-allowed" : ""}`}
                          >
                            {skill.name}
                            <span className="ml-1.5 opacity-60 text-[10px]">
                              ({skill.category})
                            </span>
                          </button>
                        );
                      })}
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-border">
                      <label className="block text-xs font-medium text-text-secondary mb-2">
                        Or create a new skill to learn
                      </label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Enter skill name..."
                          value={newLearnSkill}
                          onChange={(e) => setNewLearnSkill(e.target.value)}
                          disabled={isCreatingSkill}
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCreateSkill(newLearnSkill, "learn")}
                          disabled={!newLearnSkill.trim() || isCreatingSkill}
                          loading={isCreatingSkill}
                        >
                          Add
                        </Button>
                      </div>
                    </div>
                  </>
                )}
                <div className="flex justify-between mt-6">
                  <Button variant="outline" onClick={handleBack}>
                    Back
                  </Button>
                  <Button onClick={handleNext}>Continue</Button>
                </div>
              </Card>
            </motion.div>
          )}

          {step === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <Card
                title="Review your onboarding"
                subtitle="Step 4: Final Confirmation"
              >
                <div className="flex flex-col gap-4 text-left">
                  <div className="bg-bg p-3.5 rounded-lg border border-border">
                    <h4 className="text-xs font-bold text-accent mb-1 uppercase tracking-wider">
                      Academic Profile
                    </h4>
                    <p className="font-semibold text-sm">{department} (Year {year})</p>
                    <p className="text-xs text-text-secondary mt-1 line-clamp-2">"{bio}"</p>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-text-secondary mb-1.5 uppercase tracking-wider">
                      Skills to Teach ({selectedTeach.length})
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedTeach.length === 0 ? (
                        <span className="text-xs italic text-text-secondary">None selected</span>
                      ) : (
                        selectedTeach.map((id) => {
                          const s = availableSkills.find((x) => x.id === id);
                          return (
                            <span
                              key={id}
                              className="px-2 py-0.5 text-[10px] font-semibold bg-green-500/10 text-green-600 rounded-md border border-green-500/10"
                            >
                              {s?.name}
                            </span>
                          );
                        })
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-text-secondary mb-1.5 uppercase tracking-wider">
                      Skills to Learn ({selectedLearn.length})
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedLearn.length === 0 ? (
                        <span className="text-xs italic text-text-secondary">None selected</span>
                      ) : (
                        selectedLearn.map((id) => {
                          const s = availableSkills.find((x) => x.id === id);
                          return (
                            <span
                              key={id}
                              className="px-2 py-0.5 text-[10px] font-semibold bg-accent/10 text-accent rounded-md border border-accent/10"
                            >
                              {s?.name}
                            </span>
                          );
                        })
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex justify-between mt-8">
                  <Button variant="outline" onClick={handleBack} disabled={isSubmitting}>
                    Back
                  </Button>
                  <Button onClick={handleFinish} isLoading={isSubmitting}>
                    Complete Onboarding
                  </Button>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
