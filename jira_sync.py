import csv
import os
import sys
import requests
from datetime import datetime

# ---------------- Configuration ---------------- #
JIRA_URL = os.getenv("JIRA_URL", "").strip().strip('"').strip("'").rstrip("/")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "").strip()

if not JIRA_URL or not JIRA_TOKEN:
    print("Missing JIRA_URL or JIRA_TOKEN environment variables.")
    sys.exit(1)
# ------------------------------------------------ #

def jira_request(method, endpoint, **kwargs):
    """Wrapper for Jira REST API calls (Bearer token authentication)."""
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

def find_issue_by_summary(summary, project_key):
    """Search issue by summary text (exact match). Always return dict or None."""
    if not summary:
        return None
    jql = f'project = "{project_key}" AND summary ~ "{summary}"'
    resp = jira_request("GET", f"search?jql={jql}")
    if resp.status_code != 200:
        print(f"Warning: Jira search failed ({resp.status_code}) for summary: {summary}")
        return None

    try:
        data = resp.json()
    except ValueError:
        print(f"Warning: Invalid JSON response for summary: {summary}")
        return None

    issues = data.get("issues", [])
    for issue in issues:
        if issue.get("fields", {}).get("summary", "").strip().lower() == summary.strip().lower():
            return issue
    return None

def get_epic_link_field():
    """Auto-detect Epic Link custom field ID. Fall back silently if unauthorized."""
    try:
        resp = jira_request("GET", "field")
        if resp.status_code == 200:
            for field in resp.json():
                if field.get("name") == "Epic Link":
                    return field["id"]
        else:
            print("Using default Epic Link field: customfield_10014 (field list access denied or unavailable).")
    except Exception:
        pass
    return "customfield_10014"

def create_issue(project_key, summary, issue_type, epic_key=None, epic_link_field=None,
                 description=None, epic_name=None, writer=None):
    """Create a Jira issue of the given type."""
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description or f"Auto-created by script for summary: {summary}",
        "issuetype": {"name": issue_type},
    }

    # Add Epic Name for Epics
    if issue_type.lower() == "epic":
        fields["customfield_10004"] = epic_name or summary

    # Link Story/Task to Epic if applicable
    if epic_key and issue_type.lower() in ["story", "task"]:
        fields[epic_link_field] = epic_key

    resp = jira_request("POST", "issue", json={"fields": fields})
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if resp.status_code == 201:
        key = resp.json()["key"]
        print(f"Created {issue_type}: {key} ({summary})")
        if writer:
            writer.writerow([timestamp, "Created", key, issue_type, epic_key or "", ""])
        return key
    else:
        msg = resp.text.strip().replace("\n", " ")
        print(f"Failed to create {issue_type}: {summary} ({msg})")
        if writer:
            writer.writerow([timestamp, "Failed", "", issue_type, epic_key or "", msg])
        return None

def get_current_epic_link(issue_key, epic_link_field):
    """Fetch current Epic link value."""
    resp = jira_request("GET", f"issue/{issue_key}?fields={epic_link_field}")
    if resp.status_code == 200:
        return resp.json()["fields"].get(epic_link_field)
    return None

def update_epic_link(issue_key, epic_key, epic_link_field, writer):
    """Update Epic link for an existing story/task."""
    payload = {"fields": {epic_link_field: epic_key}}
    resp = jira_request("PUT", f"issue/{issue_key}", json=payload)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if resp.status_code == 204:
        print(f"Updated Epic link for {issue_key} -> {epic_key}")
        writer.writerow([timestamp, "Updated Link", issue_key, "Story/Task", epic_key, ""])
        return True
    else:
        msg = resp.text.strip().replace("\n", " ")
        print(f"Failed to update link for {issue_key}: {msg}")
        writer.writerow([timestamp, "Failed", issue_key, "Story/Task", epic_key, msg])
    return False

def detect_delimiter(file_path):
    """Detect CSV delimiter (tab or comma)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        line = f.readline()
        if '\t' in line:
            return '\t'
        elif ',' in line:
            return ','
        else:
            return ','

def process_csv(project_key, csv_path):
    """Main CSV processing logic."""
    epic_link_field = get_epic_link_field()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"jira_log_{timestamp_str}.csv"

    epic_cache = {}
    delimiter = detect_delimiter(csv_path)

    with open(csv_path, newline='', encoding='utf-8') as csvfile, \
         open(log_filename, "w", newline='', encoding='utf-8') as logfile:
        
        first_line = csvfile.readline().replace('\ufeff', '')
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        if not reader.fieldnames:
            print(f"Error: No header found in {csv_path}. Ensure it has the correct columns.")
            sys.exit(1)
        reader.fieldnames = [name.strip().replace('\ufeff', '') for name in reader.fieldnames]

        writer = csv.writer(logfile)
        writer.writerow(["Timestamp", "Action", "Issue Key", "Type", "Linked Epic", "Message"])

        for row in reader:
            epic_summary = row.get("Epic", "").strip()
            epic_description = row.get("Epic_Summary(customfield_10004)", "").strip()
            story_summary = row.get("Story", "").strip()
            story_description = row.get("Story_Description(description)", "").strip()
            task_summary = row.get("RE_Task", row.get("RE Task", "")).strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not (epic_summary and story_summary and task_summary):
                msg = f"Incomplete row: {row}"
                print(msg)
                writer.writerow([timestamp, "Skipped", "", "Row", "", msg])
                continue

            # --- EPIC ---
            epic_key = epic_cache.get(epic_summary)
            if epic_key:
                print(f"Epic exists (cached): {epic_key} ({epic_summary})")
                writer.writerow([timestamp, "No Change", epic_key, "Epic", "", ""])
            else:
                epic_issue = find_issue_by_summary(epic_summary, project_key)
                if isinstance(epic_issue, dict):
                    epic_key = epic_issue["key"]
                    print(f"Epic exists: {epic_key} ({epic_summary})")
                    writer.writerow([timestamp, "No Change", epic_key, "Epic", "", ""])
                elif epic_issue is None:
                    epic_key = create_issue(
                        project_key, epic_summary, "Epic",
                        description=epic_description,
                        epic_name=epic_summary,
                        writer=writer
                    )
                else:
                    print(f"Warning: Unexpected value returned for Epic '{epic_summary}': {epic_issue}")
                    writer.writerow([timestamp, "Failed", "", "Epic", "", "Unexpected response"])
                    continue

                if epic_key:
                    epic_cache[epic_summary] = epic_key

            if not epic_key:
                continue  # Skip stories/tasks if Epic creation failed

            # --- STORY ---
            story_issue = find_issue_by_summary(story_summary, project_key)
            if isinstance(story_issue, dict):
                story_key = story_issue["key"]
                current_epic = get_current_epic_link(story_key, epic_link_field)
                if current_epic != epic_key:
                    print(f"Story {story_key} linked to wrong/missing Epic ({current_epic}), fixing...")
                    update_epic_link(story_key, epic_key, epic_link_field, writer)
                else:
                    print(f"Story exists: {story_key} ({story_summary})")
                    writer.writerow([timestamp, "No Change", story_key, "Story", epic_key, ""])
            elif story_issue is None:
                story_key = create_issue(
                    project_key, story_summary, "Story",
                    epic_key=epic_key,
                    epic_link_field=epic_link_field,
                    description=story_description,
                    writer=writer
                )
            else:
                print(f"Warning: Unexpected response for Story '{story_summary}': {story_issue}")
                writer.writerow([timestamp, "Failed", "", "Story", epic_key, "Unexpected response"])

            # --- RE TASK ---
            task_issue = find_issue_by_summary(task_summary, project_key)
            if isinstance(task_issue, dict):
                task_key = task_issue["key"]
                current_epic = get_current_epic_link(task_key, epic_link_field)
                if current_epic != epic_key:
                    print(f"Task {task_key} linked to wrong/missing Epic ({current_epic}), fixing...")
                    update_epic_link(task_key, epic_key, epic_link_field, writer)
                else:
                    print(f"Task exists: {task_key} ({task_summary})")
                    writer.writerow([timestamp, "No Change", task_key, "Task", epic_key, ""])
            elif task_issue is None:
                task_key = create_issue(
                    project_key, task_summary, "Task",
                    epic_key=epic_key,
                    epic_link_field=epic_link_field,
                    writer=writer
                )
            else:
                print(f"Warning: Unexpected response for Task '{task_summary}': {task_issue}")
                writer.writerow([timestamp, "Failed", "", "Task", epic_key, "Unexpected response"])

    print(f"\nLog saved to {log_filename}")

def bulk_replace_text_in_project(project_key, old_text, new_text):
    """
    Find all issues in the given project whose summary or description contains old_text,
    and replace occurrences with new_text.

    Example:
        bulk_replace_text_in_project("NXX801THDP", 
                                     "SwReq OV NXP684 Specific UI App", 
                                     "SwReq OV NXX801 Specific UI App")
    """
    print(f"Searching in project {project_key} for text: '{old_text}'")
    jql = f'project = "{project_key}" AND (summary ~ "{old_text}" OR description ~ "{old_text}")'
    resp = jira_request("GET", f"search?jql={jql}&maxResults=500&fields=summary,description")
    if resp.status_code != 200:
        print(f"Failed to search Jira issues: {resp.status_code} {resp.text}")
        return

    data = resp.json()
    issues = data.get("issues", [])
    print(f"Found {len(issues)} issues containing '{old_text}'")

    for issue in issues:
        key = issue["key"]
        fields = issue["fields"]
        summary = fields.get("summary") or ""
        description = fields.get("description") or ""
        updated = False

        # Replace in summary
        if old_text in summary:
            summary = summary.replace(old_text, new_text)
            updated = True

        # Replace in description
        if old_text in description:
            description = description.replace(old_text, new_text)
            updated = True

        if updated:
            payload = {"fields": {"summary": summary, "description": description}}
            put_resp = jira_request("PUT", f"issue/{key}", json=payload)
            if put_resp.status_code == 204:
                print(f"Updated {key}")
            else:
                print(f"Failed to update {key}: {put_resp.status_code} {put_resp.text}")
        else:
            print(f"No change for {key}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python jira_sync.py <PROJECT_KEY> <CSV_FILENAME>")
        sys.exit(1)

    project_key = sys.argv[1]
    csv_path = sys.argv[2]

    if not os.path.exists(csv_path):
        print(f"Error: File not found - {csv_path}")
        sys.exit(1)

    print(f"Using CSV: {csv_path}")
    process_csv(project_key, csv_path)