import React from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import {
  Sparkles,
  Users,
  Calendar,
  Target,
  ArrowRight,
  CheckCircle,
  BookOpen,
  Wallet as WalletIcon,
  Brain,
  Zap,
  Globe,
  Award
} from "lucide-react";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import Footer from "../components/common/Footer";

export default function Home() {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Learning Paths",
      description: "Generate personalized roadmaps and skill gap analyses tailored to your goals."
    },
    {
      icon: Users,
      title: "Peer Mentorship",
      description: "Connect with experienced students who can teach you new skills."
    },
    {
      icon: Calendar,
      title: "Session Management",
      description: "Schedule, join, and track your 1-on-1 mentoring sessions easily."
    },
    {
      icon: WalletIcon,
      title: "Skill Coin Economy",
      description: "Earn coins by teaching and spend them to learn from others."
    },
    {
      icon: Target,
      title: "Skill Gap Analysis",
      description: "Discover what skills you need for your dream job role."
    },
    {
      icon: Award,
      title: "Progress Tracking",
      description: "Earn badges and track your learning journey over time."
    }
  ];

  const stats = [
    { value: "500+", label: "Active Learners" },
    { value: "50+", label: "Skills Available" },
    { value: "1000+", label: "Sessions Completed" },
    { value: "95%", label: "Satisfaction Rate" }
  ];

  return (
    <div className="min-h-screen bg-bg">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-bg/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
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
              <span className="font-bold text-lg tracking-tight text-text">
                Skill<span className="text-accent">Swap</span>
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/login">
                <Button variant="ghost" size="sm">Sign In</Button>
              </Link>
              <Link to="/register">
                <Button variant="primary" size="sm">Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-semibold mb-6">
                <Sparkles size={14} />
                AI-Powered Peer Learning Platform
              </div>
              
              <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-text mb-6">
                Learn Anything from<br />
                <span className="text-accent">Peer Experts</span>
              </h1>
              
              <p className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto mb-8">
                Connect with skilled students, schedule 1-on-1 sessions, and accelerate your learning with AI-powered roadmaps tailored to your goals.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link to="/register">
                  <Button variant="primary" size="lg" className="w-full sm:w-auto">
                    Start Learning Free
                    <ArrowRight size={18} className="ml-2" />
                  </Button>
                </Link>
                <Link to="/mentors">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    Browse Mentors
                  </Button>
                </Link>
              </div>
            </motion.div>

            {/* Hero Image/Visual */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="mt-16 relative"
            >
              <div className="relative mx-auto max-w-4xl">
                <div className="absolute inset-0 bg-accent/20 blur-3xl rounded-full opacity-30" />
                <div className="relative bg-bg border border-border rounded-2xl shadow-2xl p-4 md:p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-3 h-3 rounded-full bg-danger" />
                    <div className="w-3 h-3 rounded-full bg-warning" />
                    <div className="w-3 h-3 rounded-full bg-success" />
                  </div>
                  <div className="bg-bg-alt rounded-lg p-6 text-left">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center">
                        <Users className="text-accent" size={24} />
                      </div>
                      <div>
                        <p className="font-semibold text-text">Your Learning Dashboard</p>
                        <p className="text-xs text-text-secondary">Track progress, book sessions, earn rewards</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-bg p-4 rounded-lg border border-border">
                        <p className="text-2xl font-bold text-accent">12</p>
                        <p className="text-xs text-text-secondary">Sessions Booked</p>
                      </div>
                      <div className="bg-bg p-4 rounded-lg border border-border">
                        <p className="text-2xl font-bold text-success">45</p>
                        <p className="text-xs text-text-secondary">Skill Coins</p>
                      </div>
                      <div className="bg-bg p-4 rounded-lg border border-border">
                        <p className="text-2xl font-bold text-warning">8</p>
                        <p className="text-xs text-text-secondary">Badges Earned</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-bg-alt border-y border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <p className="text-3xl md:text-4xl font-bold text-accent">{stat.value}</p>
                <p className="text-sm text-text-secondary mt-1">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-text mb-4">
              Everything You Need to Learn Faster
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              Our platform combines AI-powered insights with human mentorship to create the perfect learning experience.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full hover:border-accent/40 transition-colors">
                  <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                    <feature.icon className="text-accent" size={24} />
                  </div>
                  <h3 className="text-lg font-semibold text-text mb-2">{feature.title}</h3>
                  <p className="text-sm text-text-secondary">{feature.description}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 bg-bg-alt">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-text mb-4">
              How It Works
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              Get started in three simple steps
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "1",
                title: "Create Your Profile",
                description: "Sign up and tell us what you can teach and what you want to learn.",
                icon: Users
              },
              {
                step: "2",
                title: "Connect & Learn",
                description: "Find mentors, book sessions, and start learning from peer experts.",
                icon: Zap
              },
              {
                step: "3",
                title: "Earn & Grow",
                description: "Teach others to earn coins, unlock badges, and track your progress.",
                icon: Award
              }
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2 }}
                className="text-center"
              >
                <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-4">
                  <span className="text-xl font-bold text-accent">{item.step}</span>
                </div>
                <div className="w-12 h-12 rounded-lg bg-bg border border-border flex items-center justify-center mx-auto mb-4">
                  <item.icon className="text-text-secondary" size={20} />
                </div>
                <h3 className="text-lg font-semibold text-text mb-2">{item.title}</h3>
                <p className="text-sm text-text-secondary max-w-xs mx-auto">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-accent/5 border border-accent/20 rounded-2xl p-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-text mb-4">
              Ready to Start Learning?
            </h2>
            <p className="text-lg text-text-secondary mb-8 max-w-xl mx-auto">
              Join thousands of students who are already swapping skills and accelerating their learning journey.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register">
                <Button variant="primary" size="lg" className="w-full sm:w-auto">
                  Create Free Account
                  <ArrowRight size={18} className="ml-2" />
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  Sign In
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}