"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";

/**
 * Renders a mini sparkline for the session card.
 * We draw directly on a small canvas to avoid pulling in Chart.js for
 * a tiny decorative element.
 */
function MiniSparkline({ dataPoints }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !dataPoints || dataPoints.length < 2) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    // Use just the confidence values, sampled evenly
    const step = Math.max(1, Math.floor(dataPoints.length / 60));
    const pts = dataPoints.filter((_, i) => i % step === 0);
    const values = pts.map((d) => d.confidence ?? d);

    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    ctx.beginPath();
    values.forEach((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });

    const gradient = ctx.createLinearGradient(0, 0, w, 0);
    gradient.addColorStop(0, "#6366f1");
    gradient.addColorStop(1, "#06b6d4");
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // Area fill
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    const fillGradient = ctx.createLinearGradient(0, 0, 0, h);
    fillGradient.addColorStop(0, "rgba(99,102,241,0.15)");
    fillGradient.addColorStop(1, "rgba(99,102,241,0)");
    ctx.fillStyle = fillGradient;
    ctx.fill();
  }, [dataPoints]);

  return (
    <div className="sparkline-container">
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "100%", display: "block" }}
      />
    </div>
  );
}

function getConfidenceLevel(score) {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

export default function SessionCard({ session, index, onDelete }) {
  const level = getConfidenceLevel(session.avg_confidence);
  const total =
    (session.time_high || 0) +
    (session.time_medium || 0) +
    (session.time_low || 0) || 1;

  return (
    <Link href={`/session/${session.id}`}>
      <div
        className="glass-card session-card animate-in"
        style={{ animationDelay: `${index * 60}ms` }}
      >
        <div className="session-card-header">
          <div className="session-card-info">
            <h3>{session.name || "Untitled Session"}</h3>
            <span className="session-card-date">
              {formatDate(session.date)}
            </span>
          </div>
          <div className={`confidence-badge ${level}`}>
            {Math.round(session.avg_confidence)}
          </div>
        </div>

        {/* Sparkline placeholder — filled when detail is fetched */}
        <MiniSparkline dataPoints={session.data_points || []} />

        <div className="time-breakdown">
          <div
            className="time-bar-high"
            style={{ width: `${(session.time_high / total) * 100}%` }}
          />
          <div
            className="time-bar-medium"
            style={{ width: `${(session.time_medium / total) * 100}%` }}
          />
          <div
            className="time-bar-low"
            style={{ width: `${(session.time_low / total) * 100}%` }}
          />
        </div>

        <div className="session-card-footer">
          <span className="session-card-duration">
            ⏱ {formatDuration(session.duration)}
          </span>
          <button
            className="delete-btn"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDelete(session.id);
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </Link>
  );
}
