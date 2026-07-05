import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import Card from "../components/common/Card";
import Input from "../components/common/Input";
import Button from "../components/common/Button";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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
      // 1. Call Register endpoint
      await api.post("/auth/register", {
        name,
        email,
        password,
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
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-text">
            Create your account
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Join the peer learning community and start swapping skills
          </p>
        </div>

        {/* Card for registration form */}
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
              placeholder="alex@example.com"
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
              className="w-full mt-2"
            >
              Sign Up
            </Button>
          </form>
        </Card>

        {/* Footer info link */}
        <p className="text-center text-xs text-text-secondary mt-6">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-accent hover:text-accent-hover underline"
          >
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
