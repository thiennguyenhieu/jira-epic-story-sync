import os
import sys

JIRA_URL = os.getenv("JIRA_URL", "").strip().strip('"').strip("'").rstrip("/")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "").strip()

if not JIRA_URL or not JIRA_TOKEN:
    print("Missing JIRA_URL or JIRA_TOKEN environment variables.")
    sys.exit(1)
