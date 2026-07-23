import React, { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

// Modern theme color palette for Recharts
const CHART_COLORS = [
  "#6366f1", // Indigo
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ec4899", // Pink
  "#8b5cf6", // Purple
  "#06b6d4", // Cyan
  "#3b82f6", // Blue
];

export default function ActivityCharts({ analytics }) {
  const [activeTab, setActiveTab] = useState("weekly");
  const [activeIndex, setActiveIndex] = useState(null);

  // 1. Format Weekly Activity Data
  const weeklyData = useMemo(() => {
    if (!analytics?.weekly_activity) return [];
    return Object.entries(analytics.weekly_activity).map(([day, count]) => ({
      day: day.slice(0, 3), // e.g. Mon, Tue
      fullDay: day,
      count: Number(count) || 0,
    }));
  }, [analytics]);

  // 2. Format Monthly Activity Data
  const monthlyData = useMemo(() => {
    if (!analytics?.monthly_activity) return [];
    return Object.entries(analytics.monthly_activity).map(([dateKey, count]) => ({
      date: dateKey.length > 5 ? dateKey.slice(-5) : dateKey, // e.g. 05-20 or Day 1
      fullDate: dateKey,
      count: Number(count) || 0,
    }));
  }, [analytics]);

  // 3. Format Activity Distribution Data
  const distributionData = useMemo(() => {
    if (!analytics?.activity_distribution) return [];
    return Object.entries(analytics.activity_distribution).map(([cat, val]) => ({
      name: cat.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
      rawCategory: cat,
      value: Number(val) || 0,
    }));
  }, [analytics]);

  // Custom Tooltip formatter for dark/light themes
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-popover border border-border text-popover-foreground px-3 py-2 rounded-lg shadow-lg text-xs">
          <p className="font-bold text-foreground mb-1">
            {data.payload.fullDay || data.payload.fullDate || label || data.name}
          </p>
          <p className="text-primary font-medium">
            {data.name || "Activities"}: <span className="font-bold">{data.value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Chart View Selector & Headers */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-3">
        <div>
          <h3 className="text-base font-bold text-foreground m-0">
            Activity Visualizations
          </h3>
          <p className="text-xs text-muted-foreground m-0">
            Interactive breakdown of your learning engagements
          </p>
        </div>

        <div className="flex items-center gap-1 bg-muted p-1 rounded-lg border border-border/50 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("weekly")}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeTab === "weekly"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Weekly
          </button>
          <button
            onClick={() => setActiveTab("monthly")}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeTab === "monthly"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setActiveTab("distribution")}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeTab === "distribution"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Distribution
          </button>
        </div>
      </div>

      {/* Grid Layout for Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart (Weekly or Monthly Line/Bar) */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              {activeTab === "weekly"
                ? "Weekly Activity Breakdown (Days of Week)"
                : activeTab === "monthly"
                ? "Monthly Learning Velocity & Trend"
                : "Activity Category Shares"}
            </span>
          </div>

          <div className="w-full h-64 sm:h-72">
            <ResponsiveContainer width="100%" height="100%">
              {activeTab === "weekly" ? (
                <BarChart
                  data={weeklyData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                  onMouseMove={(state) => {
                    if (state.isTooltipActive) setActiveIndex(state.activeTooltipIndex);
                    else setActiveIndex(null);
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} vertical={false} />
                  <XAxis
                    dataKey="day"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 12, fill: "currentColor" }}
                    className="text-muted-foreground"
                  />
                  <YAxis
                    allowDecimals={false}
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 12, fill: "currentColor" }}
                    className="text-muted-foreground"
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(99, 102, 241, 0.08)" }} />
                  <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "12px" }} />
                  <Bar
                    name="Activities"
                    dataKey="count"
                    radius={[6, 6, 0, 0]}
                    fill="#6366f1"
                  >
                    {weeklyData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={index === activeIndex ? "#4f46e5" : "#6366f1"}
                        opacity={activeIndex !== null && index !== activeIndex ? 0.7 : 1}
                      />
                    ))}
                  </Bar>
                </BarChart>
              ) : activeTab === "monthly" ? (
                <LineChart
                  data={monthlyData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: "currentColor" }}
                    className="text-muted-foreground"
                  />
                  <YAxis
                    allowDecimals={false}
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 12, fill: "currentColor" }}
                    className="text-muted-foreground"
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "12px" }} />
                  <Line
                    type="monotone"
                    name="Activities"
                    dataKey="count"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ r: 4, fill: "#10b981" }}
                    activeDot={{ r: 7, stroke: "#047857", strokeWidth: 2 }}
                  />
                </LineChart>
              ) : (
                <PieChart>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "12px" }} />
                  <Pie
                    data={distributionData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={85}
                    innerRadius={45}
                    paddingAngle={3}
                    label={({ name, percent }) =>
                      percent > 0.05 ? `${(percent * 100).toFixed(0)}%` : ""
                    }
                  >
                    {distributionData.map((entry, index) => (
                      <Cell
                        key={`pie-cell-${index}`}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                </PieChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Share Distribution Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
            Activity Distribution Summary
          </span>

          {distributionData.length > 0 ? (
            <div className="flex flex-col gap-3 my-auto">
              {distributionData.map((item, index) => {
                const total = distributionData.reduce((acc, curr) => acc + curr.value, 0);
                const pct = total > 0 ? Math.round((item.value / total) * 100) : 0;
                const color = CHART_COLORS[index % CHART_COLORS.length];

                return (
                  <div key={item.name} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-foreground flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full inline-block"
                          style={{ backgroundColor: color }}
                        />
                        {item.name}
                      </span>
                      <span className="text-muted-foreground font-mono">
                        {item.value} ({pct}%)
                      </span>
                    </div>
                    <div className="w-full bg-muted h-2 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-xs text-muted-foreground italic">
              No category distribution data available yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
