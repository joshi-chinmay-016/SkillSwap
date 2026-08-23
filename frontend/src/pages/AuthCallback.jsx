import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import api from "../services/api";
import { PushPin } from "../components/common/PinnedCard";
import { HandDrawnNote } from "../components/common/HandwrittenAnnotation";
import Button from "../components/common/Button";
import { AlertCircle, ArrowLeft, CheckCircle2, Loader2, Sparkles } from "lucide-react";

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const [errorMsg, setErrorMsg] = useState("");
  const [isProcessing, setIsProcessing] = useState(true);

  const loginStore = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  useEffect(() => {
    const error = searchParams.get("error");
    const ticket = searchParams.get("ticket");

    if (error) {
      setErrorMsg(error);
      setIsProcessing(false);
      return;
    }

    if (!ticket) {
      setErrorMsg("Missing authentication ticket from provider callback.");
      setIsProcessing(false);
      return;
    }

    // Exchange ticket for JWT
    const exchangeTicket = async () => {
      try {
        const res = await api.post("/auth/oauth/exchange", { ticket });
        const { access_token, user } = res.data;

        // Clean up URL parameters to keep history pristine
        window.history.replaceState({}, document.title, window.location.pathname);

        // Save authenticated session to Zustand store
        loginStore(access_token, user);

        // Redirect to dashboard (or onboarding)
        navigate("/dashboard", { replace: true });
      } catch (err) {
        console.error("OAuth ticket exchange failed:", err);
        const msg = err.response?.data?.detail || "Authentication ticket expired or invalid. Please sign in again.";
        setErrorMsg(msg);
        setIsProcessing(false);
      }
    };

    exchangeTicket();
  }, [searchParams, loginStore, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center whiteboard-grid text-text px-4 py-12 relative select-none">
      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-7 space-y-2">
          <div className="inline-flex items-center gap-2.5 mb-2">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center text-white shadow-md">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-black text-2xl tracking-tight text-text">
              Skill<span className="text-accent">Swap</span>{" "}
              <span className="font-handwriting text-xl font-bold text-rose-500 rotate-[-4deg] inline-block ml-1">
                Arena 📌
              </span>
            </span>
          </div>
        </div>

        {/* Pinned Card */}
        <div className="relative rounded-3xl border border-card-border bg-card-bg/95 backdrop-blur-xl shadow-2xl p-6 sm:p-8 text-center">
          <PushPin color={errorMsg ? "rose" : "yellow"} className="-top-3" />

          {isProcessing ? (
            <div className="py-8 space-y-4">
              <Loader2 className="w-10 h-10 text-accent animate-spin mx-auto" />
              <h3 className="text-lg font-bold text-text">
                Verifying Classroom Identity...
              </h3>
              <p className="text-xs text-text-secondary">
                Securing your authentication credentials and preparing your desk.
              </p>
            </div>
          ) : errorMsg ? (
            <div className="py-6 space-y-5">
              <div className="w-12 h-12 bg-danger/10 text-danger rounded-2xl flex items-center justify-center mx-auto border border-danger/20">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-base font-bold text-danger">
                  Sign In Could Not Be Completed
                </h3>
                <p className="text-xs text-text-secondary">
                  {errorMsg}
                </p>
              </div>

              <div className="pt-2">
                <Link to="/login">
                  <Button variant="primary" size="md" className="w-full font-bold" leftIcon={ArrowLeft}>
                    Return to Student Login
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <div className="py-8 space-y-4">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
              <h3 className="text-lg font-bold text-text">
                Welcome to SkillSwap!
              </h3>
              <p className="text-xs text-text-secondary">
                Redirecting to your classroom dashboard...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
