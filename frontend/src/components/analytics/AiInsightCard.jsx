import React, { useMemo } from "react";
import { Sparkles, Lightbulb, CheckCircle2, Zap } from "lucide-react";

export default function AiInsightCard({ analytics }) {
  const insights = useMemo(() => {
    if (!analytics) return [];

    const list = [];
    const {
      learning_trend,
      most_active_day,
      learning_velocity,
      average_per_day,
      summary,
    } = analytics;

    // 1. Trend Insight
    if (learning_trend) {
      if (learning_trend.direction === "up") {
        list.push({
          id: "trend-up",
          title: "Accelerating Growth",
          text: `Learning activity increased ${learning_trend.percentage}% this week compared to last week. Great momentum!`,
          icon: Zap,
          color: "text-emerald-500 bg-emerald-500/10",
        });
      } else if (learning_trend.direction === "down") {
        list.push({
          id: "trend-down",
          title: "Learning Reflection",
          text: `Learning activity dipped ${learning_trend.percentage}% this week. A quick study session can get you right back on track.`,
          icon: Lightbulb,
          color: "text-amber-500 bg-amber-500/10",
        });
      } else {
        list.push({
          id: "trend-stable",
          title: "Consistent Pace",
          text: "Your weekly activity has maintained a steady and consistent pace.",
          icon: CheckCircle2,
          color: "text-blue-500 bg-blue-500/10",
        });
      }
    }

    // 2. Most Active Day Insight
    if (most_active_day && most_active_day.day) {
      list.push({
        id: "active-day",
        title: "Peak Learning Day",
        text: `You learn most consistently on ${most_active_day.day}s with ${most_active_day.count} activities logged.`,
        icon: Sparkles,
        color: "text-purple-500 bg-purple-500/10",
      });
    }

    // 3. Velocity / Streak Insight
    if (learning_velocity > 0) {
      list.push({
        id: "velocity",
        title: "Learning Velocity",
        text: `You average ${learning_velocity} activities per day over the last 30 days.`,
        icon: Zap,
        color: "text-indigo-500 bg-indigo-500/10",
      });
    }

    if (summary && summary.current_streak > 0) {
      list.push({
        id: "streak",
        title: "Streak Power",
        text: `You are currently on a ${summary.current_streak}-day learning streak with ${summary.total_activities} total activities completed!`,
        icon: CheckCircle2,
        color: "text-emerald-500 bg-emerald-500/10",
      });
    }

    return list;
  }, [analytics]);

  if (!insights.length) return null;

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-xs flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <div className="p-2 rounded-lg bg-primary/10 text-primary">
          <Sparkles className="w-5 h-5" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground m-0">
            AI Learning Intelligence
          </h3>
          <p className="text-xs text-muted-foreground m-0">
            Derived insights from your activity history
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {insights.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              className="flex items-start gap-3 p-3 rounded-lg border border-border/60 bg-muted/20"
            >
              <div className={`p-1.5 rounded-md ${item.color} shrink-0 mt-0.5`}>
                <Icon className="w-4 h-4" aria-hidden="true" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-foreground m-0">
                  {item.title}
                </h4>
                <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                  {item.text}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
