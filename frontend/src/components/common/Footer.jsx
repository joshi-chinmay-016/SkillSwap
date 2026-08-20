import React from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import {
  Sparkles,
  Mail,
  ArrowUpRight,
  Heart,
  Globe,
  ShieldCheck,
  Zap,
} from "lucide-react";

function GithubIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

function LinkedinIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect width="4" height="12" x="2" y="9" />
      <circle cx="4" cy="4" r="2" />
    </svg>
  );
}

export default function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    platform: [
      { name: "Discover Mentors", to: "/mentors" },
      { name: "Sessions & Calendar", to: "/sessions" },
      { name: "Learning Roadmap", to: "/journey/roadmap" },
      { name: "Skill Gap Analyzer", to: "/journey/skill-gap" },
      { name: "Skill Coins Wallet", to: "/wallet" },
    ],
    aiMentor: [
      { name: "AI Mentor Workspace", to: "/mentor" },
      { name: "Document Knowledge", to: "/mentor/knowledge" },
      { name: "Mentor Memory", to: "/mentor/memory" },
      { name: "Peer Match Insights", to: "/ai/mentor-recommendation" },
    ],
    resources: [
      { name: "Learning Activity", to: "/activity" },
      { name: "User Dashboard", to: "/dashboard" },
      { name: "Profile & Badges", to: "/profile" },
    ],
    community: [
      { name: "GitHub Repository", href: "https://github.com/joshi-chinmay-016/SkillSwap", external: true },
      { name: "LinkedIn Connect", href: "https://www.linkedin.com/in/chinmay-joshi-59a840312/", external: true },
      { name: "Developer Email", href: "mailto:joshichinmay3201@gmail.com", external: true },
    ],
  };

  return (
    <footer className="relative bg-bg border-t border-border/70 mt-auto transition-colors duration-200 overflow-hidden">
      {/* Subtle background glow */}
      <div className="pointer-events-none absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[250px] bg-gradient-to-t from-accent/5 via-accent/2 to-transparent blur-3xl opacity-60" />

      <div className="relative max-w-7xl mx-auto px-6 sm:px-8 pt-16 pb-12">
        {/* Main Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 lg:gap-8 mb-16">
          {/* Brand Column */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="inline-flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center text-white shadow-glow group-hover:scale-105 transition-transform duration-200">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
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
              <span className="font-bold text-xl tracking-tight text-text">
                Skill<span className="text-accent">Swap</span> <span className="text-xs uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-accent ml-1">Arena</span>
              </span>
            </Link>

            <p className="text-sm text-text-secondary max-w-sm leading-relaxed">
              The premier peer-learning ecosystem. Exchange skills, schedule live sessions, build verified credibility, and accelerate your mastery with an AI-grounded mentor.
            </p>

            <div className="pt-2 flex items-center gap-3">
              <a
                href="https://github.com/joshi-chinmay-016/SkillSwap"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 rounded-xl bg-surface-elevated border border-border flex items-center justify-center text-text-secondary hover:text-accent hover:border-accent/40 transition-all duration-200 hover:-translate-y-0.5 shadow-xs"
                aria-label="GitHub"
              >
                <GithubIcon size={17} />
              </a>
              <a
                href="https://www.linkedin.com/in/chinmay-joshi-59a840312/"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 rounded-xl bg-surface-elevated border border-border flex items-center justify-center text-text-secondary hover:text-accent hover:border-accent/40 transition-all duration-200 hover:-translate-y-0.5 shadow-xs"
                aria-label="LinkedIn"
              >
                <LinkedinIcon size={17} />
              </a>
              <a
                href="mailto:joshichinmay3201@gmail.com"
                className="w-9 h-9 rounded-xl bg-surface-elevated border border-border flex items-center justify-center text-text-secondary hover:text-accent hover:border-accent/40 transition-all duration-200 hover:-translate-y-0.5 shadow-xs"
                aria-label="Email"
              >
                <Mail size={17} />
              </a>
            </div>
          </div>

          {/* Platform Column */}
          <div className="space-y-3.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-text">
              Platform
            </h4>
            <ul className="space-y-2.5">
              {footerLinks.platform.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.to}
                    className="text-xs text-text-secondary hover:text-accent transition-colors flex items-center gap-1 group"
                  >
                    <span>{link.name}</span>
                    <ArrowUpRight
                      size={12}
                      className="opacity-0 -translate-x-1 translate-y-1 group-hover:opacity-100 group-hover:translate-x-0 group-hover:translate-y-0 transition-all"
                    />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* AI Mentor Column */}
          <div className="space-y-3.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-text flex items-center gap-1.5">
              <Sparkles size={13} className="text-accent" />
              AI Mentor
            </h4>
            <ul className="space-y-2.5">
              {footerLinks.aiMentor.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.to}
                    className="text-xs text-text-secondary hover:text-accent transition-colors flex items-center gap-1 group"
                  >
                    <span>{link.name}</span>
                    <ArrowUpRight
                      size={12}
                      className="opacity-0 -translate-x-1 translate-y-1 group-hover:opacity-100 group-hover:translate-x-0 group-hover:translate-y-0 transition-all"
                    />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources & Community Column */}
          <div className="space-y-3.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-text">
              Community & Connect
            </h4>
            <ul className="space-y-2.5">
              {footerLinks.community.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-text-secondary hover:text-accent transition-colors flex items-center gap-1 group"
                  >
                    <span>{link.name}</span>
                    <ArrowUpRight
                      size={12}
                      className="opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all"
                    />
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Status Bar */}
        <div className="pt-8 border-t border-border/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-secondary">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Peer Learning Network Online</span>
          </div>

          <p className="flex items-center gap-1">
            © {currentYear} SkillSwap Arena. Built by Chinmay Joshi.
          </p>
        </div>
      </div>
    </footer>
  );
}
