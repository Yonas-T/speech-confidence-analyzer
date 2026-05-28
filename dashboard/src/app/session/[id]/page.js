"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import SummaryCards from "@/components/SummaryCards";
import ConfidenceTimeline from "@/components/ConfidenceTimeline";
import MetricRadar from "@/components/MetricRadar";
import ConfidenceDistribution from "@/components/ConfidenceDistribution";
import KeyMoments from "@/components/KeyMoments";

const API = "http://localhost:5001/api";

function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function SessionDetail({ params }) {
  const { id } = params;
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/sessions/${id}`);
        if (!res.ok) throw new Error("Session not found");
        const data = await res.json();
        setSession(data.session);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p className="loading-text">Loading session…</p>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🔍</div>
        <h2 className="empty-title">Session not found</h2>
        <p className="empty-text">
          This session may have been deleted.
        </p>
        <Link href="/" className="back-btn" style={{ marginTop: "1.5rem", display: "inline-flex" }}>
          ← Back to sessions
        </Link>
      </div>
    );
  }

  return (
    <>
      <Link href="/" className="back-btn">
        ← Back to sessions
      </Link>

      <div className="detail-header">
        <div className="detail-title">
          <h1>{session.name || "Untitled Session"}</h1>
          <p className="detail-date">{formatDate(session.date)}</p>
        </div>
      </div>

      {/* Summary row */}
      <SummaryCards session={session} />

      {/* Charts — full-width timeline, then radar + doughnut side-by-side */}
      <div className="charts-grid">
        <div className="glass-card chart-panel full-width animate-in">
          <h3 className="chart-title">
            <span className="chart-title-icon">📈</span> Confidence Over Time
          </h3>
          <ConfidenceTimeline dataPoints={session.data_points} />
        </div>

        <div className="glass-card chart-panel animate-in" style={{ animationDelay: "60ms" }}>
          <h3 className="chart-title">
            <span className="chart-title-icon">🕸️</span> Metric Breakdown
          </h3>
          <MetricRadar session={session} />
        </div>

        <div className="glass-card chart-panel animate-in" style={{ animationDelay: "120ms" }}>
          <h3 className="chart-title">
            <span className="chart-title-icon">🍩</span> Time Distribution
          </h3>
          <ConfidenceDistribution session={session} />
        </div>
      </div>

      {/* Key moments */}
      <div className="glass-card chart-panel full-width animate-in" style={{ animationDelay: "180ms" }}>
        <h3 className="chart-title">
          <span className="chart-title-icon">⭐</span> Key Moments
        </h3>
        <KeyMoments dataPoints={session.data_points} />
      </div>
    </>
  );
}
