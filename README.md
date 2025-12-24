# 🧭 JIRA Epic & Story Synchronizer

A Python tool to automatically create and link **Epics**, **Stories**, **Tasks**, and **Sub-tasks** in JIRA — based on a simple CSV file or directly through JIRA APIs.

This helps keep your project hierarchy consistent and up to date with minimal manual work.

---

## ⚙️ Setup

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Configure environment variables
(Use set on Windows or export on macOS/Linux)
```bash
set JIRA_URL=your_jira_url
set JIRA_TOKEN=your_personal_access_token
```
## 🚀 Basic Usage
Sync from CSV
```bash
python jira_sync.py <PROJECT_KEY> <CSV_FILENAME>
```
This will:
- Create missing Epics, Stories, and Tasks
- Ensure each Story/Task is correctly linked to its Epic
- Export a structured log file: jira_log_YYYYMMDD_HHMMSS.csv

## 🧩 Additional Commands
| Command | Description |
|----------|-------------|
| `python jira_sync.py --help` | Show help and all available commands |
| `python jira_sync.py --list-link-types` | List all available JIRA issue link types |
| `python jira_sync.py --list-issue-types` | List all available JIRA issue types |
| `python jira_sync.py --list-all` | Show both link types and issue types |
| `python jira_sync.py --list-sprint-issues <SPRINT_ID>` | List all Story, Task, and Bug issues in the given sprint |
| `python jira_sync.py --create-subtasks <SPRINT_ID>` | For every Story, Task, and Bug in the sprint, ensure subtasks **Implement**, **Review**, and **Test** exist |
| `python jira_sync.py --create-subtasks-for <ISSUE_KEY>` | Create subtasks (**Implement**, **Review**, **Test**) for a single issue |

| `python jira_sync.py --replace-text <PROJECT_KEY> <OLD_TEXT> <NEW_TEXT>` | Replace `OLD_TEXT` with `NEW_TEXT` in issue summaries/descriptions |
