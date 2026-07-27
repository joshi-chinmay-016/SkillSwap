import React, { useState } from "react";
import { Download, FileText, Check } from "lucide-react";

export default function ExportAnalytics({ analytics }) {
  const [downloaded, setDownloaded] = useState(false);

  const exportCSV = () => {
    if (!analytics) return;

    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Metric,Value\n";
    csvContent += `Total Activities,${analytics.summary?.total_activities || 0}\n`;
    csvContent += `Total Active Days,${analytics.summary?.total_active_days || 0}\n`;
    csvContent += `Average Activities Per Day,${analytics.average_per_day || 0}\n`;
    csvContent += `Learning Velocity,${analytics.learning_velocity || 0}\n`;
    csvContent += `Current Streak,${analytics.summary?.current_streak || 0}\n`;
    csvContent += `Longest Streak,${analytics.summary?.longest_streak || 0}\n`;
    csvContent += `Most Active Day,${analytics.most_active_day?.day || "N/A"} (${analytics.most_active_day?.count || 0} activities)\n`;
    csvContent += `Learning Trend,${analytics.learning_trend?.direction || "stable"} (${analytics.learning_trend?.percentage || 0}%)\n\n`;

    csvContent += "Weekly Day,Activity Count\n";
    if (analytics.weekly_activity) {
      Object.entries(analytics.weekly_activity).forEach(([day, count]) => {
        csvContent += `"${day}",${count}\n`;
      });
    }

    csvContent += "\nCategory,Activity Count\n";
    if (analytics.activity_distribution) {
      Object.entries(analytics.activity_distribution).forEach(([cat, count]) => {
        csvContent += `"${cat}",${count}\n`;
      });
    }

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `learning_analytics_${new Date().toISOString().slice(0, 10)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setDownloaded(true);
    setTimeout(() => setDownloaded(false), 2000);
  };

  const exportPDF = () => {
    // Print-friendly view trigger
    window.print();
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={exportCSV}
        disabled={!analytics}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors border border-border disabled:opacity-50"
        title="Export Analytics as CSV"
      >
        {downloaded ? (
          <Check className="w-3.5 h-3.5 text-emerald-500" />
        ) : (
          <Download className="w-3.5 h-3.5" />
        )}
        <span>Export CSV</span>
      </button>

      <button
        onClick={exportPDF}
        disabled={!analytics}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors border border-border disabled:opacity-50"
        title="Export or Print Analytics Report"
      >
        <FileText className="w-3.5 h-3.5" />
        <span>Export Report</span>
      </button>
    </div>
  );
}
