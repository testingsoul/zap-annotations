#!/usr/bin/env python3
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from urllib import error, request

REPORT_DIR = sys.argv[2] if len(sys.argv) > 2 else "test/output"
SEVERITIES_TO_FAIL = sys.argv[1] if len(sys.argv) > 1 else "Critical,High,Medium"
PATTERN = set(re.split(r"\s*,\s*", SEVERITIES_TO_FAIL.strip()))

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID", "")
GITHUB_EVENT_NAME = os.environ.get("GITHUB_EVENT_NAME", "")
GITHUB_EVENT_PATH = os.environ.get("GITHUB_EVENT_PATH", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API_URL = os.environ.get("GITHUB_API_URL", "https://api.github.com")

SEVERITY_ORDER = {
    "Critical": 0,
    "High": 1,
    "Medium": 2,
    "Low": 3,
    "Informational": 4,
}
SEVERITY_COLORS = {
    "Critical": "#8B0000",
    "High": "#D73A49",
    "Medium": "#FB8500",
    "Low": "#1F883D",
    "Informational": "#0969DA",
}
SEVERITY_LABELS = {
    "Critical": "🔴 Critical",
    "High": "🟠 High",
    "Medium": "🟡 Medium",
    "Low": "🟢 Low",
    "Informational": "🔵 Informational",
}


def get_artifact_download_url(repo, run_id, artifact_name, token, api_url):
    if not (repo and run_id and token):
        return ""

    url = f"{api_url}/repos/{repo}/actions/runs/{run_id}/artifacts"
    req = request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    try:
        with request.urlopen(req) as resp:
            data = json.load(resp)
        for artifact in data.get("artifacts", []):
            if artifact.get("name") == artifact_name:
                artifact_id = artifact.get("id")
                return f"https://github.com/{repo}/actions/runs/{run_id}/artifacts/{artifact_id}"
    except error.HTTPError as http_err:
        print(f"Failed to list artifacts: {http_err.code} {http_err.reason}")
    except Exception as exc:
        print(f"Error getting artifact URL: {exc}")

    return ""


def text_for(elem, name):
    for child in elem.iter():
        if child.tag and child.tag.endswith(name):
            return (child.text or "").strip()
    return ""


def read_pr_number(event_name, event_path):
    if event_name != "pull_request" or not event_path or not os.path.isfile(event_path):
        return None
    try:
        with open(event_path, "r", encoding="utf-8") as f:
            event = json.load(f)
        pr = event.get("pull_request", {})
        return pr.get("number")
    except Exception as exc:
        print(f"Could not read PR number from event payload: {exc}")
        return None


def main():
    artifact_link = get_artifact_download_url(
        GITHUB_REPOSITORY,
        GITHUB_RUN_ID,
        "zap-html-reports",
        GITHUB_TOKEN,
        GITHUB_API_URL,
    )

    print("== ZAP Annotation Action ==")
    print(f"Scanning directory: {REPORT_DIR}")
    print(f"Failing severities: {SEVERITIES_TO_FAIL}")

    alert_count = 0
    summary = (
        "### ZAP Scan Summary\n\n"
        f"Detected alerts matching severities: **{SEVERITIES_TO_FAIL}**\n\n"
    )

    xml_files = glob.glob(os.path.join(REPORT_DIR, "zapreport-*.xml"))
    if not xml_files:
        print("No zapreport-*.xml files found.")

    for xml_file in xml_files:
        summary += (
            f"#### Report File: `{xml_file}`\n\n"
            "| Alert | Severity | Occurrences |\n"
            "| --- | --- | --- |\n"
        )

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except Exception as exc:
            print(f"Failed to parse {xml_file}: {exc}")
            continue

        alertitems = [el for el in root.iter() if el.tag and el.tag.endswith("alertitem")]
        matched_alerts = {}

        for alert in alertitems:
            risk_full = text_for(alert, "riskdesc")
            risk = risk_full.split()[0] if risk_full else ""
            name = text_for(alert, "name") or "Unknown"

            if risk in PATTERN:
                alert_count += 1
                key = (name, risk)
                matched_alerts[key] = matched_alerts.get(key, 0) + 1

        sorted_alerts = sorted(
            matched_alerts.items(),
            key=lambda x: (SEVERITY_ORDER.get(x[0][1], 99), x[0][0].lower()),
        )

        for (name, risk), occurrences in sorted_alerts:
            severity_cell = SEVERITY_LABELS.get(risk, f"⚪ {risk}")
            summary += f"| {name} | {severity_cell} | {occurrences} |\n"

        if not sorted_alerts:
            summary += "| No matching alerts | - | - |\n"

        summary += "\n"

    if artifact_link:
        summary += f"📄 Download HTML report from [artifact]({artifact_link})\n\n"

    summary += f"---\nTotal matching alerts: **{alert_count}**"
    print(summary)

    pr_number = read_pr_number(GITHUB_EVENT_NAME, GITHUB_EVENT_PATH)
    if pr_number and GITHUB_TOKEN and GITHUB_REPOSITORY:
        print("Posting PR summary comment...")
        url = f"{GITHUB_API_URL}/repos/{GITHUB_REPOSITORY}/issues/{pr_number}/comments"
        data = json.dumps({"body": summary}).encode("utf-8")
        req = request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        try:
            with request.urlopen(req) as resp:
                resp.read()
        except error.HTTPError as http_err:
            print(f"Failed to post PR comment: {http_err.code} {http_err.reason}")
    else:
        print("PR context/token not available; skipping PR comment.")

    if alert_count > 0:
        print(f"ZAP alerts found above threshold: {alert_count}")
        sys.exit(1)

    print("No alerts exceed threshold.")
    sys.exit(0)


if __name__ == "__main__":
    main()
