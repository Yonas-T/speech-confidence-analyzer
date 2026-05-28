"use client";

import { Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const METRIC_LABELS = [
  "Visibility",
  "Posture",
  "Orientation",
  "Hand Openness",
  "Gesture",
  "Head Position",
];

const METRIC_KEYS = [
  "avg_visibility",
  "avg_posture_straightness",
  "avg_body_orientation",
  "avg_hand_openness",
  "avg_gesture_activity",
  "avg_head_position",
];

export default function MetricRadar({ session }) {
  if (!session) return null;

  const values = METRIC_KEYS.map((k) => session[k] ?? 0);

  const data = {
    labels: METRIC_LABELS,
    datasets: [
      {
        label: "Score",
        data: values,
        backgroundColor: "rgba(99, 102, 241, 0.15)",
        borderColor: "#6366f1",
        borderWidth: 2,
        pointBackgroundColor: "#6366f1",
        pointBorderColor: "#0f172a",
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
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
          label: (ctx) => `${ctx.label}: ${ctx.parsed.r.toFixed(1)}`,
        },
      },
    },
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          color: "#64748b",
          backdropColor: "transparent",
          stepSize: 20,
          font: { size: 10 },
        },
        grid: {
          color: "rgba(100, 116, 139, 0.15)",
        },
        angleLines: {
          color: "rgba(100, 116, 139, 0.12)",
        },
        pointLabels: {
          color: "#94a3b8",
          font: { size: 12, weight: 500 },
        },
      },
    },
  };

  return (
    <div className="chart-container radar">
      <Radar data={data} options={options} />
    </div>
  );
}
