"use client";

function getLevel(score) {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

const CARDS = [
  { key: "avg_confidence", label: "Average", icon: "📊" },
  { key: "max_confidence", label: "Maximum", icon: "🔺" },
  { key: "min_confidence", label: "Minimum", icon: "🔻" },
  { key: "duration", label: "Duration", icon: "⏱", isDuration: true },
];

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function SummaryCards({ session }) {
  if (!session) return null;

  return (
    <div className="summary-grid">
      {CARDS.map((card, i) => {
        const value = session[card.key] ?? 0;
        const level = card.isDuration ? "neutral" : getLevel(value);
        const display = card.isDuration
          ? formatDuration(value)
          : `${value.toFixed(1)}%`;

        return (
          <div
            key={card.key}
            className="glass-card summary-card animate-in"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className="summary-card-icon">{card.icon}</div>
            <div className={`summary-card-value ${level}`}>{display}</div>
            <div className="summary-card-label">{card.label}</div>
          </div>
        );
      })}
    </div>
  );
}
