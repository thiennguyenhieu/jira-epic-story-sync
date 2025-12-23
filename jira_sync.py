import sys
from csv_utils import process_csv
from jira_api import get_link_types, get_issue_types
from text_utils import bulk_replace_text_in_project
from board_utils import (
    get_sprint_issues,
    ensure_subtasks_for_sprint,
    ensure_subtasks_for_issue
)

# ------------------------------------------------------------
# HELP MESSAGE
# ------------------------------------------------------------
def print_help():
    print("\nUsage:")
    print("  python jira_sync.py --help")
    print("      Show this help message and exit.\n")

    print("  python jira_sync.py --list-link-types")
    print("      List all available Jira issue link types.\n")

    print("  python jira_sync.py --list-issue-types")
    print("      List all available Jira issue types (Epic, Story, Task, etc.).\n")

    print("  python jira_sync.py --list-all")
    print("      Show both link types and issue types.\n")

    print("  python jira_sync.py --list-sprint-issues <SPRINT_ID>")
    print("      List all Story, Task, and Bug issues in the given sprint ID.\n")

    print("  python jira_sync.py --create-subtasks <SPRINT_ID>")
    print("      For every Story, Task, and Bug in the sprint, create subtasks:")
    print("      'Implement', 'Review', and 'Test' if they do not already exist.\n")

    print("  python jira_sync.py --create-subtasks-for <ISSUE_KEY>")
    print("      Create subtasks ('Implement', 'Review', 'Test') for a single Jira issue.\n")

    print("  python jira_sync.py --replace-text <PROJECT_KEY> <OLD_TEXT> <NEW_TEXT>")
    print("      Find all issues in the project where summary or description contains OLD_TEXT")
    print("      and replace it with NEW_TEXT.\n")

    print("  python jira_sync.py <PROJECT_KEY> <CSV_FILENAME>")
    print("      Process a CSV file to create or update Epics, Stories, and Tasks in Jira.\n")


# ------------------------------------------------------------
# COMMAND EXECUTION
# ------------------------------------------------------------
def main():
    args = sys.argv[1:]
    if not args or args[0] in ["--help", "-h"]:
        print_help()
        sys.exit(0)

    command = args[0]

    # --- Simple dispatch pattern ---
    if command == "--list-link-types":
        print("=== Link types ===")
        print(get_link_types())

    elif command == "--list-issue-types":
        print("=== Issue types ===")
        print(get_issue_types())

    elif command == "--list-all":
        print("=== Link types ===")
        print(get_link_types())
        print("\n=== Issue types ===")
        print(get_issue_types())

    elif command == "--list-sprint-issues":
        if len(args) != 2:
            print("❌ Usage: python jira_sync.py --list-sprint-issues <SPRINT_ID>")
            sys.exit(1)
        sprint_id = args[1]
        get_sprint_issues(sprint_id)

    elif command == "--create-subtasks":
        if len(args) != 2:
            print("❌ Usage: python jira_sync.py --create-subtasks <SPRINT_ID>")
            sys.exit(1)
        sprint_id = args[1]
        ensure_subtasks_for_sprint(sprint_id)

    elif command == "--create-subtasks-for":
        if len(args) != 2:
            print("❌ Usage: python jira_sync.py --create-subtasks-for <ISSUE_KEY>")
            sys.exit(1)
        issue_key = args[1]
        ensure_subtasks_for_issue(issue_key)

    elif command == "--replace-text":
        if len(args) != 4:
            print("❌ Usage: python jira_sync.py --replace-text <PROJECT_KEY> <OLD_TEXT> <NEW_TEXT>")
            sys.exit(1)
        project, old_text, new_text = args[1], args[2], args[3]
        bulk_replace_text_in_project(project, old_text, new_text)

    elif len(args) == 2:
        project_key, csv_path = args
        process_csv(project_key, csv_path)

    else:
        print(f"❌ Unknown or invalid command: {' '.join(args)}")
        print("Use '--help' for usage details.")
        sys.exit(1)


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
