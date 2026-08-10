#!/usr/bin/env python3
"""
NetSage AI - Web Dashboard & API Server
======================================
Serves the NetSage AI web dashboard and provides REST API endpoints
for live diagnostics, rule checking, case exploration, and human review governance.
"""

import os
import sys
import csv
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Setup engine import path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from rule_checker import DeterministicRuleChecker
from diagnose_runner import DiagnosticEngine

DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DIR = os.path.join(BASE_DIR, "web")

diagnostic_engine = DiagnosticEngine()
rule_checker = DeterministicRuleChecker()

session_reviews = []


class NetSageRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving web assets and REST APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/cases":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            cases_csv = os.path.join(DATA_DIR, "cases.csv")
            cases = []
            if os.path.exists(cases_csv):
                with open(cases_csv, mode="r", encoding="utf-8") as f:
                    cases = list(csv.DictReader(f))
            self.wfile.write(json.dumps(cases, indent=2).encode("utf-8"))

        elif path == "/api/responsible-ai":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            rai_csv = os.path.join(DATA_DIR, "responsible_ai_log.csv")
            logs = []
            if os.path.exists(rai_csv):
                with open(rai_csv, mode="r", encoding="utf-8") as f:
                    logs = list(csv.DictReader(f))
            self.wfile.write(json.dumps(logs, indent=2).encode("utf-8"))

        elif path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            summary_json = os.path.join(DATA_DIR, "evaluation_summary.json")
            stats = {}
            if os.path.exists(summary_json):
                with open(summary_json, mode="r", encoding="utf-8") as f:
                    stats = json.load(f)
            self.wfile.write(json.dumps(stats, indent=2).encode("utf-8"))

        elif path == "/api/reviews":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(session_reviews, indent=2).encode("utf-8"))

        else:
            # Serve static files from web/
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if path == "/api/diagnose":
            symptom = payload.get("symptom", "")
            topology = payload.get("topology_note", "")
            show_outputs = payload.get("show_outputs", "")

            # Run deterministic check
            rule_findings = rule_checker.run_all_checks(symptom, topology, show_outputs)
            rule_dicts = [f.to_dict() for f in rule_findings]

            # Generate AI diagnosis
            case_mock = {
                "symptom": symptom,
                "topology_note": topology,
                "show_outputs": show_outputs,
                "expected_fault": payload.get("expected_fault", "Detected from show command patterns"),
                "osi_layer": payload.get("osi_layer", "Layer 3 - Network"),
                "concept_tag": payload.get("concept_tag", "GENERAL"),
                "severity": payload.get("severity", "Medium"),
                "suggested_fix": payload.get("suggested_fix", "configure terminal\n! Review commands\nend")
            }
            ai_diag = diagnostic_engine._generate_ai_diagnosis(case_mock, rule_findings)

            response_data = {
                "rule_findings": rule_dicts,
                "ai_diagnosis": ai_diag
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))

        elif path == "/api/review":
            session_reviews.append(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "total_reviews": len(session_reviews)}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


def start_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, NetSageRequestHandler)
    print(f"\n========================================================")
    print(f"  🚀 NetSage AI Web Server Active")
    print(f"  🌐 Access Dashboard: http://localhost:{port}")
    print(f"========================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping NetSage AI Server...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_server(port)
