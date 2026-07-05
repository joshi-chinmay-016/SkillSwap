import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import Card from "../components/common/Card";
import Input from "../components/common/Input";
import Button from "../components/common/Button";

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
      
      // Navigate to dashboard
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
    <div className="min-h-screen flex items-center justify-center bg-bg px-4 select-none">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="w-full max-w-md"
      >
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-accent/10 text-accent mb-3">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-text">
            Sign in to SkillSwap
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            AI-driven peer learning and skill sharing marketplace
          </p>
        </div>

        {/* Card containing login form */}
        <Card className="shadow-md">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {apiError && (
              <div
                className="p-3 text-xs bg-danger/10 border border-danger/20 text-danger rounded-md font-medium text-left"
                role="alert"
              >
                {apiError}
              </div>
            )}

            <Input
              label="Email Address"
              type="email"
              placeholder="you@example.com"
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
              className="w-full mt-2"
            >
              Sign In
            </Button>
          </form>
        </Card>

        {/* Footer info link */}
        <p className="text-center text-xs text-text-secondary mt-6">
          Don't have an account?{" "}
          <Link
            to="/register"
            className="font-semibold text-accent hover:text-accent-hover underline"
          >
            Create an account
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
