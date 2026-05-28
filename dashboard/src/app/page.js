"use client";

import { useEffect, useState } from "react";
import SessionCard from "@/components/SessionCard";

const API = "http://localhost:5001/api";

export default function Home() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API}/sessions`);
      if (!res.ok) throw new Error("Failed to fetch sessions");
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleDelete = async (id) => {
    if (!confirm("Delete this session?")) return;
    try {
      await fetch(`${API}/sessions/${id}`, { method: "DELETE" });
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p className="loading-text">Loading sessions…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-icon">⚠️</div>
        <h2 className="empty-title">Cannot connect to API</h2>
        <p className="empty-text">
          Make sure the Flask server is running on{" "}
          <code>localhost:5001</code>.
          <br />
          <code style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
            cd src && python -m api.server
          </code>
        </p>
      </div>
    );
  }

  return (
    <>
      <h1 className="page-title">Your Sessions</h1>
      <p className="page-subtitle">
        Review past speaking sessions and track confidence improvements
      </p>

      {sessions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🎙️</div>
          <h2 className="empty-title">No sessions yet</h2>
          <p className="empty-text">
            Run the Speech Confidence Analyzer from the terminal to record
            your first 4-minute session.
            <br />
            <code style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
              cd src && python speech_confidence_analyzer.py
            </code>
          </p>
        </div>
      ) : (
        <div className="sessions-grid">
          {sessions.map((session, i) => (
            <SessionCard
              key={session.id}
              session={session}
              index={i}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </>
  );
}
