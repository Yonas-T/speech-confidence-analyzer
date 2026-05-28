"use client";

/**
 * Shows the best and worst 10-second windows from the session.
 */
export default function KeyMoments({ dataPoints }) {
  if (!dataPoints || dataPoints.length < 5) return null;

  // Find the best and worst 10-second (≈ 20 data points at 500 ms) sliding windows
  const windowSize = Math.min(20, Math.floor(dataPoints.length / 2));

  let bestAvg = -1;
  let bestStart = 0;
  let worstAvg = 101;
  let worstStart = 0;

  for (let i = 0; i <= dataPoints.length - windowSize; i++) {
    const slice = dataPoints.slice(i, i + windowSize);
    const avg =
      slice.reduce((s, dp) => s + dp.confidence, 0) / slice.length;

    if (avg > bestAvg) {
      bestAvg = avg;
      bestStart = i;
    }
    if (avg < worstAvg) {
      worstAvg = avg;
      worstStart = i;
    }
  }

  function formatTime(ms) {
    const sec = Math.round(ms / 1000);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  const bestTs = dataPoints[bestStart]?.timestamp ?? 0;
  const bestEndTs =
    dataPoints[Math.min(bestStart + windowSize - 1, dataPoints.length - 1)]
      ?.timestamp ?? 0;

  const worstTs = dataPoints[worstStart]?.timestamp ?? 0;
  const worstEndTs =
    dataPoints[Math.min(worstStart + windowSize - 1, dataPoints.length - 1)]
      ?.timestamp ?? 0;

  return (
    <div className="moments-grid">
      <div className="glass-card moment-card animate-in">
        <div className="moment-icon best">🏆</div>
        <div className="moment-details">
          <h4>Best Moment</h4>
          <p>
            {formatTime(bestTs)} – {formatTime(bestEndTs)}
          </p>
        </div>
        <span className="moment-score high">{bestAvg.toFixed(1)}%</span>
      </div>

      <div className="glass-card moment-card animate-in" style={{ animationDelay: "60ms" }}>
        <div className="moment-icon worst">⚠️</div>
        <div className="moment-details">
          <h4>Needs Work</h4>
          <p>
            {formatTime(worstTs)} – {formatTime(worstEndTs)}
          </p>
        </div>
        <span className="moment-score low">{worstAvg.toFixed(1)}%</span>
      </div>
    </div>
  );
}
