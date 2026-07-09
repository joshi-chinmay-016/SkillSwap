import React from "react";
import { Mail, ExternalLink } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-bg-alt border-t border-border mt-auto">
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* Branding */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center text-white">
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
              <span className="font-bold text-lg">Skill<span className="text-accent">Swap</span></span>
            </div>
            <p className="text-xs text-text-secondary mb-4">
              AI-driven peer learning platform for students to share knowledge and grow together.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">
              Quick Links
            </h3>
            <ul className="space-y-2">
              <li>
                <a href="/mentors" className="text-xs text-text-secondary hover:text-accent transition-colors">
                  Find Mentors
                </a>
              </li>
              <li>
                <a href="/journey/roadmap" className="text-xs text-text-secondary hover:text-accent transition-colors">
                  Learning Roadmap
                </a>
              </li>
              <li>
                <a href="/sessions" className="text-xs text-text-secondary hover:text-accent transition-colors">
                  Sessions
                </a>
              </li>
              <li>
                <a href="/wallet" className="text-xs text-text-secondary hover:text-accent transition-colors">
                  Wallet
                </a>
              </li>
            </ul>
          </div>

          {/* Legal & Contact */}
          <div>
            <h3 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">
              Legal & Contact
            </h3>
            <ul className="space-y-2">
              <li>
                <a href="/terms" className="text-xs text-text-secondary hover:text-accent transition-colors">
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="/privacy" className="text-xs text-text-secondary hover:text-accent transition-colors">
                  Privacy Policy
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-border flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-text-secondary">
            © 2026 SkillSwap. Built by Chinmay Joshi, Bengaluru.
          </p>
          <div className="flex items-center gap-4">
            <a
              href="mailto:chinmay.joshi@example.com"
              className="text-text-secondary hover:text-accent transition-colors"
              aria-label="Email"
            >
              <Mail size={16} />
            </a>
            <a
              href="https://github.com/joshi-chinmay-016"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-secondary hover:text-accent transition-colors"
              aria-label="GitHub"
            >
              <ExternalLink size={16} />
            </a>
            <a
              href="https://linkedin.com/in/chinmayjoshi"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-secondary hover:text-accent transition-colors"
              aria-label="LinkedIn"
            >
              <ExternalLink size={16} />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
