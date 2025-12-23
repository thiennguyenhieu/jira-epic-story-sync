from datetime import datetime
from jira_api import jira_request

def get_existing_links(issue_key):
    resp = jira_request("GET", f"issue/{issue_key}?fields=issuelinks")
    if resp.status_code == 200:
        return resp.json()["fields"].get("issuelinks", [])
    return []

def is_already_linked(issue_key, target_key, link_type="Needs"):
    for link in get_existing_links(issue_key):
        name = link.get("type", {}).get("name", "")
        inward = link.get("inwardIssue", {}).get("key", "")
        outward = link.get("outwardIssue", {}).get("key", "")
        if name == link_type and (inward == target_key or outward == target_key):
            return True
    return False

def create_issue_link(inward_key, outward_key, link_type="Needs", writer=None):
    payload = {"type": {"name": link_type}, "inwardIssue": {"key": inward_key}, "outwardIssue": {"key": outward_key}}
    resp = jira_request("POST", "issueLink", json=payload)
    if resp.status_code == 201:
        print(f"Linked {inward_key} → {outward_key} ({link_type})")
        if writer:
            writer.writerow([datetime.now(), "Created Link", inward_key, "Link", outward_key, link_type])
        return True
    else:
        print(f"Failed to link {inward_key} → {outward_key}: {resp.text[:100]}")
        return False
