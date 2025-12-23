from jira_api import jira_request

def bulk_replace_text_in_project(project_key, old_text, new_text):
    jql = f'project = "{project_key}" AND (summary ~ "{old_text}" OR description ~ "{old_text}")'
    resp = jira_request("GET", f"search?jql={jql}&maxResults=500&fields=summary,description")
    if resp.status_code != 200:
        print(f"Failed: {resp.status_code}")
        return

    for issue in resp.json().get("issues", []):
        key = issue["key"]
        fields = issue["fields"]
        summary = fields.get("summary", "")
        description = fields.get("description", "")
        updated = False

        if old_text in summary:
            summary = summary.replace(old_text, new_text)
            updated = True
        if old_text in description:
            description = description.replace(old_text, new_text)
            updated = True

        if updated:
            put_resp = jira_request("PUT", f"issue/{key}", json={"fields": {"summary": summary, "description": description}})
            print(f"Updated {key}" if put_resp.status_code == 204 else f"Failed {key}: {put_resp.text[:100]}")
