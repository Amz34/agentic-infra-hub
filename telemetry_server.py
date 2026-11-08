#!/usr/bin/env python3
"""
Central Agentic Telemetry & Orchestration API Server
Runs on port 8999, providing real-time fleet health, run triggers,
and GitHub synchronization status.
"""
import os
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path("/home/ubuntu/agy-argon-home/.gemini/antigravity-cli/scratch/agentic-infra-hub")
FLEET_HEALTH_FILE = BASE_DIR / "fleet_health.json"
AUDIT_LOG_FILE = BASE_DIR / "audit_trail.jsonl"
MANIFEST_FILE = BASE_DIR / "last_run_manifest.json"
PORT = 8999


class TelemetryHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "UP", "service": "Agentic Infra Control Plane"})
        elif self.path == "/fleet":
            if FLEET_HEALTH_FILE.exists():
                with open(FLEET_HEALTH_FILE, "r") as f:
                    data = json.load(f)
                self._send_json(200, data)
            else:
                self._send_json(404, {"error": "Fleet health data not yet generated"})
        elif self.path == "/manifest":
            if MANIFEST_FILE.exists():
                with open(MANIFEST_FILE, "r") as f:
                    data = json.load(f)
                self._send_json(200, data)
            else:
                self._send_json(404, {"error": "Manifest not found"})
        elif self.path == "/audit":
            records = []
            if AUDIT_LOG_FILE.exists():
                with open(AUDIT_LOG_FILE, "r") as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line.strip()))
            self._send_json(200, {"count": len(records), "recent": records[-20:]})
        else:
            self._send_json(200, {
                "service": "Autonomous FDE & Agentic AI Orchestrator API",
                "endpoints": ["/health", "/fleet", "/manifest", "/audit"],
                "trigger_url": "POST /trigger"
            })

    def do_POST(self):
        if self.path == "/trigger":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = {}
            if body:
                try:
                    payload = json.loads(body)
                except Exception:
                    pass

            task = payload.get("task", "API-triggered autonomous execution cycle")
            cmd = f"python3 {BASE_DIR}/agentic_engine.py --task '{task}'"
            res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            self._send_json(200, {
                "triggered_task": task,
                "exit_code": res.returncode,
                "output": res.stdout[-400:] if res.stdout else res.stderr[-400:]
            })
        else:
            self._send_json(404, {"error": "Endpoint not found"})


def run():
    server = HTTPServer(("127.0.0.1", PORT), TelemetryHandler)
    print(f"🚀 Telemetry Server listening on http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
