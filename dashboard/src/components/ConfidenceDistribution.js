"use client";

import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

export default function ConfidenceDistribution({ session }) {
  if (!session) return null;

  const high = session.time_high || 0;
  const medium = session.time_medium || 0;
  const low = session.time_low || 0;
  const total = high + medium + low || 1;

  const data = {
    labels: ["High (>70)", "Medium (40–70)", "Low (<40)"],
    datasets: [
      {
        data: [high, medium, low],
        backgroundColor: [
          "rgba(16, 185, 129, 0.75)",
          "rgba(245, 158, 11, 0.75)",
          "rgba(239, 68, 68, 0.75)",
        ],
        borderColor: [
          "rgba(16, 185, 129, 1)",
          "rgba(245, 158, 11, 1)",
          "rgba(239, 68, 68, 1)",
        ],
        borderWidth: 2,
        hoverOffset: 8,
        spacing: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "65%",
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          color: "#94a3b8",
          padding: 16,
          usePointStyle: true,
          pointStyleWidth: 10,
          font: { size: 12 },
        },
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleColor: "#f1f5f9",
        bodyColor: "#94a3b8",
        borderColor: "rgba(100, 116, 139, 0.3)",
        borderWidth: 1,
        cornerRadius: 8,
        padding: 10,
        callbacks: {
          label: (ctx) => {
            const secs = ctx.raw;
            const pct = ((secs / total) * 100).toFixed(1);
            return `${ctx.label}: ${secs}s (${pct}%)`;
          },
        },
      },
    },
  };

  return (
    <div className="chart-container doughnut">
      <Doughnut data={data} options={options} />
    </div>
  );
}
