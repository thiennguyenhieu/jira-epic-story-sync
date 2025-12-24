import csv
import sys
from datetime import datetime

from issue_utils import (
    find_issue_by_summary,
    create_issue,
    get_epic_link_field,
    get_current_epic_link,
    update_epic_link,
)

from link_utils import (
    is_already_linked,
    create_issue_link,
)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def detect_delimiter(path):
    """Detect CSV delimiter (tab or comma)."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        line = f.readline()
        return "\t" if "\t" in line else ","


# ------------------------------------------------------------
# Main CSV processing
# ------------------------------------------------------------
def process_csv(project_key, csv_path):
    epic_link_field = get_epic_link_field()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"jira_log_{timestamp_str}.csv"

    epic_cache = {}
    delimiter = detect_delimiter(csv_path)

    with open(csv_path, newline="", encoding="utf-8", errors="ignore") as csvfile, \
         open(log_filename, "w", newline="", encoding="utf-8") as logfile:

        reader = csv.DictReader(csvfile, delimiter=delimiter)
        if not reader.fieldnames:
            print(f"Error: No header found in {csv_path}")
            sys.exit(1)

        # Clean BOM / spaces
        reader.fieldnames = [h.strip().replace("\ufeff", "") for h in reader.fieldnames]

        writer = csv.writer(logfile)
        writer.writerow(["Timestamp", "Action", "Issue Key", "Type", "Linked Epic", "Message"])

        for row in reader:
            timestamp = now()

            epic_summary = row.get("Epic", "").strip()
            epic_description = row.get("Epic_Summary(customfield_10004)", "").strip()
            epic_upper_link = row.get("Epic_Upper_Link", "").strip()

            story_summary = row.get("Story", "").strip()
            story_description = row.get("Story_Description(description)", "").strip()
            story_upper_link = row.get("Story_Upper_Link", "").strip()

            task_summary = row.get("RE_Task", row.get("RE Task", "")).strip()

            if not (epic_summary and story_summary and task_summary):
                msg = f"Incomplete row: {row}"
                print(msg)
                writer.writerow([timestamp, "Skipped", "", "Row", "", msg])
                continue

            # ------------------------------------------------
            # EPIC
            # ------------------------------------------------
            epic_key = epic_cache.get(epic_summary)
            if not epic_key:
                epic_issue = find_issue_by_summary(epic_summary, project_key)
                if isinstance(epic_issue, dict):
                    epic_key = epic_issue["key"]
                    writer.writerow([timestamp, "No Change", epic_key, "Epic", "", ""])
                else:
                    epic_key = create_issue(
                        project_key,
                        epic_summary,
                        "Epic",
                        description=epic_description,
                        epic_name=epic_summary,
                        writer=writer,
                    )

                if epic_key:
                    epic_cache[epic_summary] = epic_key

            if not epic_key:
                continue

            # Epic upper link
            if epic_upper_link:
                if not is_already_linked(epic_key, epic_upper_link, "Needs"):
                    create_issue_link(epic_key, epic_upper_link, "Needs", writer)
                else:
                    writer.writerow([timestamp, "Link Exists", epic_key, "Link", epic_upper_link, "Already linked"])

            # ------------------------------------------------
            # STORY
            # ------------------------------------------------
            story_issue = find_issue_by_summary(story_summary, project_key)
            if isinstance(story_issue, dict):
                story_key = story_issue["key"]
                current_epic = get_current_epic_link(story_key, epic_link_field)
                if current_epic != epic_key:
                    update_epic_link(story_key, epic_key, epic_link_field, writer)
                else:
                    writer.writerow([timestamp, "No Change", story_key, "Story", epic_key, ""])
            else:
                story_key = create_issue(
                    project_key,
                    story_summary,
                    "Story",
                    epic_key=epic_key,
                    epic_link_field=epic_link_field,
                    description=story_description,
                    writer=writer,
                )

            if not story_key:
                continue

            if story_upper_link:
                if not is_already_linked(story_key, story_upper_link, "Needs"):
                    create_issue_link(story_key, story_upper_link, "Needs", writer)
                else:
                    writer.writerow([timestamp, "Link Exists", story_key, "Link", story_upper_link, "Already linked"])

            # ------------------------------------------------
            # TASK
            # ------------------------------------------------
            task_issue = find_issue_by_summary(task_summary, project_key)
            if isinstance(task_issue, dict):
                task_key = task_issue["key"]
                current_epic = get_current_epic_link(task_key, epic_link_field)
                if current_epic != epic_key:
                    update_epic_link(task_key, epic_key, epic_link_field, writer)
                else:
                    writer.writerow([timestamp, "No Change", task_key, "Task", epic_key, ""])
            else:
                task_key = create_issue(
                    project_key,
                    task_summary,
                    "Task",
                    epic_key=epic_key,
                    epic_link_field=epic_link_field,
                    writer=writer,
                )

    print(f"\nLog saved to {log_filename}")
