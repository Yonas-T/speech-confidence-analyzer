"""
Speech Confidence Analyzer

Features:
  • YOLO11n-pose real-time body-language analysis
  • 6-metric scoring system (visibility, posture, orientation, hand openness,
    gesture activity, head position)
  • 4-minute session with countdown timer
  • Per-500 ms data logging to SQLite via models.database
"""

import cv2
from ultralytics import YOLO
import numpy as np
from collections import deque
import time
import uuid
from datetime import datetime

from models.database import init_db, save_session

SESSION_DURATION_S = 240 # 4 minutes
LOG_INTERVAL_MS    = 500 # save a data point every 500 ms
HISTORY_LEN        = 45 # frames kept for gesture velocity


class SpeechConfidenceAnalyzer:
    def __init__(self, model_path="yolo11n-pose.pt", camera_index=0):
        self.model = YOLO(model_path)
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.skeleton = [
            (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9),
            (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13),
            (13, 15), (12, 14), (14, 16),
        ]

        self.pose_history = deque(maxlen=HISTORY_LEN)

        self.session_id: str = ""
        self.session_name: str = ""
        self.session_start: float = 0.0
        self.data_points: list[dict] = []
        self.last_log_time: float = 0.0
        self.last_metrics: dict = {}

        print(f"Model loaded: {model_path}")

    @staticmethod
    def to_numpy(tensor):
        if isinstance(tensor, np.ndarray):
            return tensor
        return tensor.cpu().numpy()

    @staticmethod
    def calculate_angle(p1, p2, p3):
        v1, v2 = p1 - p2, p3 - p2
        cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        return float(np.degrees(np.arccos(np.clip(cos_a, -1.0, 1.0))))

    def analyze_posture(self, kpts_np, confs_np):
        """Return (overall_confidence, metrics_dict) with 6 individual scores."""
        default_metrics = dict(
            visibility=0, posture_straightness=0, body_orientation=0,
            hand_openness=0, gesture_activity=0, head_position=0,
        )

        if kpts_np is None or len(kpts_np) < 17:
            return 40.0, default_metrics

        kpts_np = self.to_numpy(kpts_np)
        confs_np = self.to_numpy(confs_np)

        nose        = kpts_np[0]
        l_shoulder  = kpts_np[5]
        r_shoulder  = kpts_np[6]
        l_wrist     = kpts_np[9]
        r_wrist     = kpts_np[10]
        l_hip       = kpts_np[11]
        r_hip       = kpts_np[12]

        visible_keypoints = float(np.sum(confs_np > 0.4))
        visibility = (visible_keypoints / 17.0) * 100.0
        if visibility < 65:
            low = max(20, visibility * 0.65)
            metrics = {**default_metrics, "visibility": round(visibility, 1)}
            return float(np.clip(low, 15, 98)), metrics

        mid_shoulder = (l_shoulder + r_shoulder) / 2
        mid_hip      = (l_hip + r_hip) / 2
        spine_vec    = mid_hip - mid_shoulder
        vertical     = np.array([0, 1])
        cos_tilt     = np.dot(spine_vec, vertical) / (np.linalg.norm(spine_vec) + 1e-6)
        tilt_angle   = np.degrees(np.arccos(np.clip(abs(cos_tilt), 0, 1)))
        posture_straightness = float(np.clip(100 - tilt_angle * 4, 15, 100))

        shoulder_width = np.linalg.norm(l_shoulder - r_shoulder)
        body_vector    = mid_hip - mid_shoulder
        aspect_ratio   = shoulder_width / (np.linalg.norm(body_vector) + 1e-6)
        body_orientation = float(np.clip(aspect_ratio * 340, 0, 100))

        body_center       = (mid_shoulder + mid_hip) / 2
        wrist_center      = (l_wrist + r_wrist) / 2
        hand_to_body_dist = np.linalg.norm(wrist_center - body_center)
        wrist_to_wrist    = np.linalg.norm(l_wrist - r_wrist)

        closed_factor = 1.0
        if wrist_to_wrist < 90:
            closed_factor = 0.45
        elif hand_to_body_dist < 140:
            closed_factor = 0.65

        hand_openness = float(np.clip(hand_to_body_dist * 4.2, 0, 100) * closed_factor)

        gesture_activity = 45.0
        if len(self.pose_history) > 10:
            prev = self.pose_history[-10]
            movement = (np.linalg.norm(l_wrist - prev[9])
                        + np.linalg.norm(r_wrist - prev[10])) * 24
            gesture_activity = float(np.clip(38 + movement * 8.5, 0, 97))

        head_y     = nose[1]
        shoulder_y = (l_shoulder[1] + r_shoulder[1]) / 2
        head_rel   = head_y - shoulder_y  # positive: head below shoulders

        if head_rel > 25:
            head_position = float(max(15, 88 - head_rel * 2.4))
        else:
            head_position = float(96 - head_rel * 1.6)
        head_position = float(np.clip(head_position, 0, 100))

        scores  = [visibility, posture_straightness, body_orientation,
                   hand_openness, gesture_activity, head_position]
        weights = [0.15, 0.20, 0.20, 0.18, 0.15, 0.12]
        confidence = float(np.clip(np.average(scores, weights=weights), 15, 98))

        metrics = dict(
            visibility=round(visibility, 1),
            posture_straightness=round(posture_straightness, 1),
            body_orientation=round(body_orientation, 1),
            hand_openness=round(hand_openness, 1),
            gesture_activity=round(gesture_activity, 1),
            head_position=round(head_position, 1),
        )

        return confidence, metrics

    @staticmethod
    def get_confidence_color(score):
        if score >= 72:
            return (0, 255, 0) # green
        elif score >= 48:
            return (0, 255, 255) # yellow
        return (0, 0, 255) # red

    def draw_skeleton(self, frame, kpts, confs):
        kpts_np  = self.to_numpy(kpts)
        confs_np = self.to_numpy(confs)

        for (start, end) in self.skeleton:
            if confs_np[start] > 0.4 and confs_np[end] > 0.4:
                pt1 = tuple(map(int, kpts_np[start]))
                pt2 = tuple(map(int, kpts_np[end]))
                cv2.line(frame, pt1, pt2, (255, 255, 0), 3)

        for i, (x, y) in enumerate(kpts_np):
            if confs_np[i] > 0.4:
                cv2.circle(frame, (int(x), int(y)), 6, (0, 0, 255), -1)
                cv2.circle(frame, (int(x), int(y)), 8, (255, 255, 255), 2)

    def draw_timer(self, frame, remaining_s):
        mins = int(remaining_s) // 60
        secs = int(remaining_s) % 60
        timer_text = f"{mins}:{secs:02d}"
        color = (255, 255, 255) if remaining_s > 30 else (0, 140, 255)
        cv2.putText(frame, timer_text, (frame.shape[1] - 180, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, color, 4)

    def draw_metrics_sidebar(self, frame, metrics):
        labels = [
            ("VIS", "visibility"),
            ("POST", "posture_straightness"),
            ("ORIENT", "body_orientation"),
            ("HANDS", "hand_openness"),
            ("GESTURE", "gesture_activity"),
            ("HEAD", "head_position"),
        ]
        start_y = 160
        bar_w = 160
        for i, (label, key) in enumerate(labels):
            y = start_y + i * 40
            val = metrics.get(key, 0)
            color = self.get_confidence_color(val)
            cv2.putText(frame, f"{label}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.rectangle(frame, (100, y - 14), (100 + bar_w, y + 4), (50, 50, 50), -1)

            fill_w = int(bar_w * val / 100)
            cv2.rectangle(frame, (100, y - 14), (100 + fill_w, y + 4), color, -1)
            cv2.putText(frame, f"{val:.0f}", (100 + bar_w + 8, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    def _start_session(self):
        self.session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.session_start = time.time()
        self.data_points = []
        self.last_log_time = 0.0
        self.last_metrics = {}

        name = input("Enter a name for this session (or press Enter to skip): ").strip()
        self.session_name = name if name else f"Session {datetime.now().strftime('%b %d %H:%M')}"

        init_db()
        print(f"\n{'='*50}")
        print(f"  Session: {self.session_name}")
        print(f"  ID:      {self.session_id}")
        print(f"  Duration: {SESSION_DURATION_S // 60} minutes")
        print(f"{'='*50}\n")
        print("Press 'q' to stop early.  Camera starting…\n")

    def _log_data_point(self, confidence, metrics, elapsed_ms):
        if elapsed_ms - self.last_log_time >= LOG_INTERVAL_MS:
            self.data_points.append(dict(
                timestamp=int(elapsed_ms),
                confidence=round(confidence, 2),
                **{k: round(v, 2) for k, v in metrics.items()},
            ))
            self.last_log_time = elapsed_ms

    def _save_session(self, actual_duration_s):
        if not self.data_points:
            print("No data recorded — nothing to save.")
            return

        confidences = [dp["confidence"] for dp in self.data_points]

        step_s = LOG_INTERVAL_MS / 1000.0
        time_high   = int(sum(step_s for c in confidences if c > 70))
        time_medium = int(sum(step_s for c in confidences if 40 <= c <= 70))
        time_low    = int(sum(step_s for c in confidences if c < 40))

        def avg_metric(key):
            vals = [dp[key] for dp in self.data_points]
            return round(sum(vals) / len(vals), 2) if vals else 0.0

        session_data = dict(
            id=self.session_id,
            name=self.session_name,
            date=datetime.now().isoformat(),
            duration=int(actual_duration_s),
            avg_confidence=round(sum(confidences) / len(confidences), 2),
            max_confidence=round(max(confidences), 2),
            min_confidence=round(min(confidences), 2),
            time_high=time_high,
            time_medium=time_medium,
            time_low=time_low,
            avg_visibility=avg_metric("visibility"),
            avg_posture_straightness=avg_metric("posture_straightness"),
            avg_body_orientation=avg_metric("body_orientation"),
            avg_hand_openness=avg_metric("hand_openness"),
            avg_gesture_activity=avg_metric("gesture_activity"),
            avg_head_position=avg_metric("head_position"),
            data_points=self.data_points,
        )

        save_session(session_data)
        print(f"\n{'='*50}")
        print(f"  Session saved!  ({len(self.data_points)} data points)")
        print(f"  Avg confidence : {session_data['avg_confidence']:.1f}")
        print(f"  Max / Min      : {session_data['max_confidence']:.1f} / {session_data['min_confidence']:.1f}")
        print(f"  Time H/M/L     : {time_high}s / {time_medium}s / {time_low}s")
        print(f"{'='*50}\n")

    def run(self):
        self._start_session()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            elapsed_s  = time.time() - self.session_start
            remaining  = max(0, SESSION_DURATION_S - elapsed_s)
            elapsed_ms = elapsed_s * 1000

            if remaining <= 0:
                print("\nTime's up!")
                break

            results = self.model(frame, conf=0.45, verbose=False)

            confidence_score = 50.0
            metrics = dict(
                visibility=0, posture_straightness=0, body_orientation=0,
                hand_openness=0, gesture_activity=0, head_position=0,
            )

            for result in results:
                if result.keypoints is not None and len(result.keypoints) > 0:
                    kpts  = result.keypoints.xy[0]
                    confs = result.keypoints.conf[0]
                    kpts_np = self.to_numpy(kpts)
                    self.pose_history.append(kpts_np)

                    confidence_score, metrics = self.analyze_posture(kpts_np, confs)
                    self.draw_skeleton(frame, kpts, confs)

                    if result.boxes is not None:
                        x1, y1, x2, y2 = map(int, result.boxes.xyxy[0])
                        color = self.get_confidence_color(confidence_score)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

            self.last_metrics = metrics
            self._log_data_point(confidence_score, metrics, elapsed_ms)

            color = self.get_confidence_color(confidence_score)
            cv2.putText(frame, f"Confidence: {confidence_score:.1f}%", (20, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.3, color, 3)

            if confidence_score < 42:
                cv2.putText(frame, "LOW CONFIDENCE - Head up, open posture & gesture!",
                            (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 0, 255), 3)
            elif confidence_score < 65:
                cv2.putText(frame, "Head up  |  Face camera  |  Open hands",
                            (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            else:
                cv2.putText(frame, "Good confident posture!",
                            (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            self.draw_timer(frame, remaining)
            self.draw_metrics_sidebar(frame, metrics)

            cv2.putText(frame, f"Session: {self.session_name}", (20, 660),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (200, 200, 200), 2)
            cv2.putText(frame, "Speech Confidence Analyzer", (20, 700),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.95, (255, 255, 255), 2)

            cv2.imshow("Speech Confidence Analyzer - YOLO Pose", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        actual_duration = time.time() - self.session_start
        self._save_session(actual_duration)
        self.release()

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
        print("Session ended.")


if __name__ == "__main__":
    analyzer = SpeechConfidenceAnalyzer(model_path="yolo11n-pose.pt")
    analyzer.run()