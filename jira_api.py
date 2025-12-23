import requests
from datetime import datetime
from config import JIRA_URL, JIRA_TOKEN

def jira_request(method, endpoint, **kwargs):
    """Wrapper for Jira REST API calls (supports both /rest/api/2 and /rest/agile/1.0)."""
    endpoint = endpoint.lstrip("/")
    if endpoint.startswith("rest/agile/"):
        url = f"{JIRA_URL}/{endpoint}"
    elif endpoint.startswith("rest/api/"):
        url = f"{JIRA_URL}/{endpoint}"
    else:
        url = f"{JIRA_URL}/rest/api/2/{endpoint}"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JIRA_TOKEN}",
    }

    resp = requests.request(method, url, headers=headers, **kwargs)
    if resp.status_code >= 400:
        print(f"{method} {endpoint} failed: {resp.status_code} {resp.text[:200]}")
    return resp

def get_epic_link_field():
    """Auto-detect Epic Link field or default."""
    resp = jira_request("GET", "field")
    if resp.status_code == 200:
        for field in resp.json():
            if field.get("name") == "Epic Link":
                return field["id"]
    print("Using default Epic Link field: customfield_10014")
    return "customfield_10014"

def get_issue_types():
    """Return available issue types."""
    resp = jira_request("GET", "issuetype")
    if resp.status_code == 200:
        types = resp.json()
        return [t["name"] for t in types]
    return []

def get_link_types():
    """Return available issue link types."""
    resp = jira_request("GET", "issueLinkType")
    if resp.status_code == 200:
        types = resp.json().get("issueLinkTypes", [])
        return [t["name"] for t in types]
    return []
