#!/usr/bin/env python3
"""
Autonomous Infra Fleet Watchdog & Health Aggregator
Scans centralized ops logs, detects silent failures/token expirations,
and updates GitHub-ready health telemetry.
"""
import os
import sys
import json
import glob
from datetime import datetime, timezone
from pathlib import Path

OPS_LOG_DIR = Path("/home/ubuntu/ops/logs")
REPORT_PATH = Path("/home/ubuntu/agy-argon-home/.gemini/antigravity-cli/scratch/agentic-infra-hub/fleet_health.json")


def scan_logs():
    findings = []
    total_scanned = 0

    if not OPS_LOG_DIR.exists():
        return {"status": "NO_OPS_DIR", "findings": [], "total_scanned": 0}

    log_files = glob.glob(str(OPS_LOG_DIR / "*.log"))
    for log_file in log_files:
        total_scanned += 1
        name = Path(log_file).name
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                last_lines = lines[-50:] if len(lines) >= 50 else lines
                
                # Check for critical errors or warnings in recent output
                for idx, line in enumerate(reversed(last_lines)):
                    lower = line.lower()
                    if any(term in lower for term in ["traceback", "fatal", "unauthorized", "expired", "401 client error", "ratelimit"]):
                        findings.append({
                            "log": name,
                            "snippet": line.strip()[:160],
                            "recent_line_offset": idx
                        })
                        break
        except Exception as e:
            continue

    return {
        "status": "HEALTHY" if len(findings) == 0 else "WARNINGS_DETECTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_logs_scanned": total_scanned,
        "anomalies_detected": len(findings),
        "details": findings[:10]  # Cap top 10
    }


def main():
    report = scan_logs()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[{report['timestamp']}] Fleet Watchdog Scan Completed: {report['status']} ({report['anomalies_detected']} anomalies across {report['total_logs_scanned']} logs)")
    if report["details"]:
        print("\nTop Active Alerts:")
        for alert in report["details"]:
            print(f"  - [{alert['log']}] -> {alert['snippet']}")


if __name__ == "__main__":
    main()
