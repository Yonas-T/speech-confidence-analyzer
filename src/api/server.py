"""
Flask REST API for the Speaker Confidence dashboard.

Endpoints:
    GET    /api/health          – health check
    GET    /api/sessions        – list all sessions
    GET    /api/sessions/<id>   – session detail with data points
    DELETE /api/sessions/<id>   – remove a session

Run:
    cd src && python -m api.server
"""

import sys
import os

# Ensure the `src/` directory is on the path so we can import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify
from flask_cors import CORS
from models.database import init_db, get_all_sessions, get_session, delete_session

app = Flask(__name__)
CORS(app)  # Allow requests from Next.js on localhost:3000

# Initialise the database tables on startup
init_db()


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/sessions")
def list_sessions():
    sessions = get_all_sessions()
    return jsonify({"sessions": sessions})


@app.route("/api/sessions/<session_id>")
def session_detail(session_id):
    session = get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"session": session})


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def remove_session(session_id):
    deleted = delete_session(session_id)
    if not deleted:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"message": "Session deleted"})


if __name__ == "__main__":
    print("Starting Speaker Confidence API on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=True)
