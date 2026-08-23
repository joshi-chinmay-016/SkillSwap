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
import { ArrowRight, Sparkles } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const loginStore = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const validate = () => {
    const newErrors = {};
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

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");

    if (!validate()) return;

    setIsLoading(true);
    try {
      // 1. Authenticate with credentials
      const authResponse = await api.post("/auth/login", {
        email,
        password,
      });

      const token = authResponse.data.access_token;

      // 2. Fetch current user profiles
      const userResponse = await api.get("/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const user = userResponse.data;

      // 3. Set store state and redirect
      loginStore(token, user);
      navigate("/dashboard");
    } catch (err) {
      console.error("Login failure:", err);
      const msg = err.response?.data?.detail || "Invalid email or password. Please try again.";
      setApiError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center whiteboard-grid text-text px-4 select-none relative py-12">
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
            Welcome to the Classroom
          </h2>
          <div className="flex items-center justify-center gap-2 pt-0.5">
            <span className="text-xs text-text-secondary">Sign in to start swapping skills</span>
            <HandDrawnNote color="rose" rotate="-2deg" className="text-sm font-bold">
              ✦ Zero fees!
            </HandDrawnNote>
          </div>
        </div>

        {/* Pinned Card containing login form & OAuth */}
        <div className="relative rounded-3xl border border-card-border bg-card-bg/95 backdrop-blur-xl shadow-2xl p-6 sm:p-8 text-left transition-all duration-300">
          <PushPin color="yellow" className="-top-3" />

          {/* Hand-drawn badge */}
          <div className="absolute -top-3 right-6 font-handwriting text-sm font-bold text-amber-900 dark:text-amber-300 bg-yellow-100 dark:bg-yellow-950 px-2.5 py-0.5 rounded-lg border border-yellow-300 dark:border-yellow-700 rotate-3 shadow-xs">
            Student Desk 📌
          </div>

          {/* Social OAuth Buttons */}
          <OAuthButtons actionText="Sign In" />

          {/* Traditional Form */}
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
              label="Email Address"
              type="email"
              placeholder="you@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              disabled={isLoading}
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
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
              Sign In to Classroom Desk
            </Button>
          </form>
        </div>

        {/* Footer info link */}
        <p className="text-center text-xs text-text-secondary mt-6">
          Don&apos;t have an account yet?{" "}
          <Link
            to="/register"
            className="font-bold text-accent hover:text-accent-hover underline"
          >
            Claim your free desk 📌
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
