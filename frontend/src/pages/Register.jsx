import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import Input from "../components/common/Input";
import Button from "../components/common/Button";
import { PushPin } from "../components/common/PinnedCard";
import { HandDrawnNote } from "../components/common/HandwrittenAnnotation";
import OAuthButtons from "../components/auth/OAuthButtons";
import { AVATAR_OPTIONS } from "../utils/avatars";
import { ArrowRight, Sparkles } from "lucide-react";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [selectedAvatar, setSelectedAvatar] = useState(AVATAR_OPTIONS[0]);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const loginStore = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const validate = () => {
    const newErrors = {};
    if (!name.trim()) {
      newErrors.name = "Full name is required";
    }

    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = "Invalid email format";
    }

    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");

    if (!validate()) return;

    setIsLoading(true);
    try {
      // 1. Call Register endpoint with selected avatar
      await api.post("/auth/register", {
        name,
        email,
        password,
        avatar_url: selectedAvatar.url,
      });

      // 2. Auto-login on success
      const authResponse = await api.post("/auth/login", {
        email,
        password,
      });

      const token = authResponse.data.access_token;

      // 3. Fetch user info
      const userResponse = await api.get("/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const user = userResponse.data;

      // 4. Save credentials and redirect to onboarding
      loginStore(token, user);
      navigate("/onboarding");
    } catch (err) {
      console.error("Registration failure:", err);
      const msg = err.response?.data?.detail || "Registration failed. Email might already be taken.";
      setApiError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center whiteboard-grid text-text px-4 py-12 select-none relative">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="w-full max-w-md relative z-10"
      >
        {/* Brand Header */}
        <div className="text-center mb-6 space-y-2">
          <Link to="/" className="inline-flex items-center gap-2.5 mb-2 group">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center text-white shadow-md group-hover:rotate-6 transition-transform duration-200">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-black text-2xl tracking-tight text-text">
              Skill<span className="text-accent">Swap</span>{" "}
              <span className="font-handwriting text-xl font-bold text-rose-500 rotate-[-4deg] inline-block ml-1">
                Arena 📌
              </span>
            </span>
          </Link>

          <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-text">
            Enroll in the Classroom
          </h2>
          <div className="flex items-center justify-center gap-2 pt-0.5">
            <span className="text-xs text-text-secondary">Join student peer mentorship</span>
            <HandDrawnNote color="rose" rotate="-2deg" className="text-sm font-bold">
              ✦ 100% Free Desk!
            </HandDrawnNote>
          </div>
        </div>

        {/* Pinned Card containing registration form */}
        <div className="relative rounded-3xl border border-card-border bg-card-bg/95 backdrop-blur-xl shadow-2xl p-6 sm:p-8 text-left transition-all duration-300">
          <PushPin color="cyan" className="-top-3" />

          {/* Hand-drawn badge */}
          <div className="absolute -top-3 right-6 font-handwriting text-sm font-bold text-sky-900 dark:text-sky-300 bg-sky-100 dark:bg-sky-950 px-2.5 py-0.5 rounded-lg border border-sky-300 dark:border-sky-700 rotate-2 shadow-xs">
            Student Enrollment 📌
          </div>

          {/* Social OAuth Buttons */}
          <OAuthButtons actionText="Sign Up" />

          <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-2">
            {apiError && (
              <div
                className="p-3 text-xs bg-danger/10 border border-danger/20 text-danger rounded-xl font-medium text-left"
                role="alert"
              >
                {apiError}
              </div>
            )}

            <Input
              label="Full Name"
              type="text"
              placeholder="Alex Johnson"
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={errors.name}
              disabled={isLoading}
            />

            <Input
              label="Email Address"
              type="email"
              placeholder="alex@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              disabled={isLoading}
            />

            {/* Avatar Picker */}
            <div className="space-y-1.5 text-left">
              <label className="block text-xs font-bold text-text-secondary">
                Choose your classroom avatar
              </label>
              <div className="grid grid-cols-6 gap-2 p-2 bg-bg-alt/70 rounded-2xl border border-border/80">
                {AVATAR_OPTIONS.map((avatar) => (
                  <button
                    key={avatar.id}
                    type="button"
                    onClick={() => setSelectedAvatar(avatar)}
                    className={`
                      relative w-full aspect-square rounded-full overflow-hidden
                      transition-all duration-150 cursor-pointer
                      ${
                        selectedAvatar.id === avatar.id
                          ? "ring-2 ring-accent ring-offset-2 ring-offset-bg scale-110 shadow-glow"
                          : "hover:scale-105 opacity-65 hover:opacity-100"
                      }
                    `}
                  >
                    <img
                      src={avatar.url}
                      alt={avatar.emoji}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            </div>

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              disabled={isLoading}
            />

            <Input
              label="Confirm Password"
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              error={errors.confirmPassword}
              disabled={isLoading}
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading}
              className="w-full mt-2 shadow-glow font-bold"
              rightIcon={ArrowRight}
            >
              Sign Up & Claim Desk
            </Button>
          </form>
        </div>

        {/* Footer info link */}
        <p className="text-center text-xs text-text-secondary mt-6">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-bold text-accent hover:text-accent-hover underline"
          >
            Sign in to desk
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
