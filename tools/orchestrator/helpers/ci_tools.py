"""Helpers for querying CI status and triggering repair flows."""
from __future__ import annotations

import os
import requests

GITHUB_API = "https://api.github.com"


def fetch_latest_run(repo: str, workflow: str, token: str | None = None) -> dict | None:
    token = token or os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow}/runs?per_page=1"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    runs = response.json().get("workflow_runs", [])
    return runs[0] if runs else None


def summarize_run(run: dict | None) -> str:
    if not run:
        return "No CI runs recorded."
    conclusion = run.get("conclusion") or run.get("status")
    html_url = run.get("html_url", "")
    return f"Latest workflow {conclusion} — {html_url}".strip()
