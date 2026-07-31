import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

// Route guards
import ProtectedRoute from "../components/auth/ProtectedRoute";
import PublicRoute from "../components/auth/PublicRoute";

// Layout
import AppLayout from "../layouts/AppLayout";

// Pages
import Home from "../pages/Home";
import Login from "../pages/Login";
import Register from "../pages/Register";
import Onboarding from "../pages/Onboarding";
import Dashboard from "../pages/Dashboard";
import MentorList from "../pages/MentorList";
import MentorDetail from "../pages/MentorDetail";
import Sessions from "../pages/Sessions";
import SessionDetail from "../pages/SessionDetail";
import Roadmap from "../pages/Roadmap";
import SkillGap from "../pages/SkillGap";
import Profile from "../pages/Profile";
import Wallet from "../pages/Wallet";
import AIChat from "../pages/AIChat";
import MentorRecommendation from "../pages/MentorRecommendation";
import LearningJourney from "../pages/LearningJourney";
import SessionPage from "../pages/SessionPage";
import ActivityFeed from "../pages/ActivityFeed";
import AIMentorPage from "../pages/AIMentorPage";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public Pages */}
      <Route path="/" element={<Home />} />

      {/* Guest/Auth Pages (Redirect to dashboard if logged in) */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      {/* Authenticated Pages */}
      <Route element={<ProtectedRoute />}>
        {/* Onboarding is full-screen */}
        <Route path="/onboarding" element={<Onboarding />} />

        {/* Dashboard and Core Sections have AppLayout (Header + Sidebar) */}
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/mentor" element={<AIMentorPage />} />
          <Route path="/mentors" element={<MentorList />} />
          <Route path="/mentors/:id" element={<MentorDetail />} />
          <Route path="/sessions" element={<Sessions />} />
          <Route path="/sessions/:id" element={<SessionDetail />} />
          <Route path="/journey/roadmap" element={<Roadmap />} />
          <Route path="/journey/skill-gap" element={<SkillGap />} />
          <Route path="/journey/:id" element={<LearningJourney />} />
          <Route path="/journeys/:journeyId/sessions" element={<LearningJourney />} />
          <Route path="/learning-sessions/:sessionId" element={<SessionPage />} />
          <Route path="/activity" element={<ActivityFeed />} />
          <Route path="/ai/chat" element={<AIChat />} />
          <Route path="/ai/mentor-recommendation" element={<MentorRecommendation />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/wallet" element={<Wallet />} />
        </Route>
      </Route>


      {/* Fallback redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}