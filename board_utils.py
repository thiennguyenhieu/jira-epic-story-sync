from jira_api import jira_request
from datetime import datetime

# Configurable subtask templates
REQUIRED_SUBTASKS = ["[Task] Implement", "[Task] Review", "[Task] Test"]

def get_sprint_issues(sprint_id, include_types=None):
    """
    Get all Story, Task, and Bug issues from a given sprint (by sprint ID).
    This does NOT depend on board or sprint state.

    Example:
        get_sprint_issues(54188)
        get_sprint_issues(54188, include_types=["Story", "Task", "Bug"])
    """
    include_types = include_types or ["Story", "Task", "Bug"]

    print(f"Fetching issues for sprint ID {sprint_id}...")

    # Fetch all issues in the sprint
    resp = jira_request("GET", f"/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=500&expand=subtasks")
    if resp.status_code != 200:
        print(f"Failed to fetch sprint issues: {resp.status_code} {resp.text}")
        return []

    issues = resp.json().get("issues", [])
    result = []
    for issue in issues:
        fields = issue.get("fields", {})
        issue_type = fields.get("issuetype", {}).get("name", "")
        if issue_type.lower() in [t.lower() for t in include_types]:
            result.append({
                "key": issue["key"],
                "summary": fields.get("summary", ""),
                "type": issue_type,
                "status": fields.get("status", {}).get("name", ""),
                "subtasks": fields.get("subtasks", []),
            })

    print(f"Found {len(result)} {', '.join(include_types)} issues in sprint {sprint_id}.")
    for r in result:
        print(f" - {r['key']} [{r['type']}] {r['summary']} ({r['status']})")
    return result


def ensure_subtasks_for_issue(issue_key, subtasks=None):
    """
    Ensure the given issue has required subtasks.
    Optionally pass existing subtasks (to skip extra GET calls).
    """
    print(f"\nChecking subtasks for {issue_key}...")

    existing_subs = []
    if subtasks is not None:
        existing_subs = [s["fields"]["summary"].strip().lower() for s in subtasks]
    else:
        # Fetch subtasks if not provided
        resp = jira_request("GET", f"issue/{issue_key}?fields=subtasks,issuetype,summary")
        if resp.status_code != 200:
            print(f"  ❌ Failed to fetch subtasks for {issue_key}: {resp.status_code}")
            return
        fields = resp.json().get("fields", {})
        existing_subs = [s["fields"]["summary"].strip().lower() for s in fields.get("subtasks", [])]

    for sub_name in REQUIRED_SUBTASKS:
        if sub_name.lower() in existing_subs:
            print(f"  ✅ Sub-task '{sub_name}' already exists.")
            continue

        payload = {
            "fields": {
                "project": {"key": issue_key.split("-")[0]},
                "parent": {"key": issue_key},
                "summary": sub_name,
                "issuetype": {"name": "Sub Task"},
                "description": f"Auto-created sub-task '{sub_name}' for {issue_key}"
            }
        }

        resp = jira_request("POST", "issue", json=payload)
        if resp.status_code == 201:
            sub_key = resp.json()["key"]
            print(f"  ➕ Created sub-task: {sub_key} ({sub_name})")
        else:
            print(f"  ❌ Failed to create sub-task '{sub_name}': {resp.status_code} {resp.text[:200]}")

    print(f"✅ Finished ensuring subtasks for {issue_key}")


def ensure_subtasks_for_sprint(sprint_id):
    """
    For each Story, Task, or Bug in the given sprint,
    ensure required subtasks (Implement, Review, Test) exist.
    """
    issues = get_sprint_issues(sprint_id)
    if not issues:
        print("No issues found in sprint.")
        return

    print(f"\n🧩 Processing {len(issues)} issues from sprint {sprint_id}...\n")

    for issue in issues:
        ensure_subtasks_for_issue(issue["key"], subtasks=issue.get("subtasks", []))

    print("\n✅ Sub-task creation completed for all issues in sprint.\n")
