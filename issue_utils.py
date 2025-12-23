from datetime import datetime
from jira_api import jira_request, get_epic_link_field

def find_issue_by_summary(summary, project_key):
    jql = f'project = "{project_key}" AND summary ~ "{summary}"'
    resp = jira_request("GET", f"search?jql={jql}")
    if resp.status_code == 200:
        for issue in resp.json().get("issues", []):
            if issue["fields"]["summary"].strip().lower() == summary.strip().lower():
                return issue
    return None

def create_issue(project_key, summary, issue_type, epic_key=None, epic_link_field=None,
                 description=None, epic_name=None, writer=None):
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description or f"Auto-created: {summary}",
        "issuetype": {"name": issue_type},
    }
    if issue_type.lower() == "epic":
        fields["customfield_10004"] = epic_name or summary
    if epic_key and issue_type.lower() in ["story", "task"]:
        fields[epic_link_field] = epic_key

    resp = jira_request("POST", "issue", json={"fields": fields})
    if resp.status_code == 201:
        key = resp.json()["key"]
        print(f"Created {issue_type}: {key} ({summary})")
        if writer:
            writer.writerow([datetime.now(), "Created", key, issue_type, epic_key or "", ""])
        return key
    else:
        print(f"Failed to create {issue_type}: {summary}")
        return None

def get_current_epic_link(issue_key, epic_link_field):
    resp = jira_request("GET", f"issue/{issue_key}?fields={epic_link_field}")
    if resp.status_code == 200:
        return resp.json()["fields"].get(epic_link_field)
    return None

def update_epic_link(issue_key, epic_key, epic_link_field, writer=None):
    payload = {"fields": {epic_link_field: epic_key}}
    resp = jira_request("PUT", f"issue/{issue_key}", json=payload)
    if resp.status_code == 204:
        print(f"Updated Epic link for {issue_key} → {epic_key}")
        if writer:
            writer.writerow([datetime.now(), "Updated Link", issue_key, "Story/Task", epic_key, ""])
        return True
    else:
        print(f"Failed to update link for {issue_key}: {resp.text[:100]}")
        return False
