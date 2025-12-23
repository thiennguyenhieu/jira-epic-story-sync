import csv
from datetime import datetime
from issue_utils import *
from link_utils import *

def detect_delimiter(path):
    with open(path, 'r', encoding='utf-8') as f:
        line = f.readline()
        return '\t' if '\t' in line else ','

def process_csv(project_key, csv_path):
    epic_link_field = get_epic_link_field()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"jira_log_{timestamp_str}.csv"
    delimiter = detect_delimiter(csv_path)
    epic_cache = {}

    with open(csv_path, newline='', encoding='utf-8') as csvfile, open(log_filename, "w", newline='', encoding='utf-8') as logfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        writer = csv.writer(logfile)
        writer.writerow(["Timestamp", "Action", "Issue Key", "Type", "Linked Epic", "Message"])

        for row in reader:
            epic_summary = row.get("Epic", "").strip()
            story_summary = row.get("Story", "").strip()
            task_summary = row.get("RE_Task", "").strip()
            if not (epic_summary and story_summary and task_summary):
                continue

            # Epic logic here...
            # (reuse functions from issue_utils and link_utils)

    print(f"\nLog saved to {log_filename}")
