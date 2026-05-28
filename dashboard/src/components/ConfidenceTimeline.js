"use client";

import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

/**
 * Confidence score over time (0 → session end).
 * Renders two horizontal threshold bands at 70 and 40.
 */
export default function ConfidenceTimeline({ dataPoints }) {
  if (!dataPoints || dataPoints.length === 0) return null;

  // Sample to max ~300 points for performance
  const step = Math.max(1, Math.floor(dataPoints.length / 300));
  const sampled = dataPoints.filter((_, i) => i % step === 0);

  const labels = sampled.map((dp) => {
    const sec = Math.round(dp.timestamp / 1000);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  });

  const data = {
    labels,
    datasets: [
      {
        label: "Confidence",
        data: sampled.map((dp) => dp.confidence),
        borderColor: "#6366f1",
        backgroundColor: "rgba(99, 102, 241, 0.08)",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#6366f1",
        fill: true,
        tension: 0.35,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleColor: "#f1f5f9",
        bodyColor: "#94a3b8",
        borderColor: "rgba(100, 116, 139, 0.3)",
        borderWidth: 1,
        cornerRadius: 8,
        padding: 10,
        callbacks: {
          label: (ctx) => `Confidence: ${ctx.parsed.y.toFixed(1)}%`,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#64748b",
          maxTicksLimit: 12,
          font: { size: 11 },
        },
        grid: { color: "rgba(100,116,139,0.08)" },
      },
      y: {
        min: 0,
        max: 100,
        ticks: {
          color: "#64748b",
          stepSize: 20,
          font: { size: 11 },
        },
        grid: { color: "rgba(100,116,139,0.08)" },
      },
    },
  };

  return (
    <div className="chart-container timeline">
      <Line data={data} options={options} />
    </div>
  );
}
