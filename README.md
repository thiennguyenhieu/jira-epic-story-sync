# JIRA Epic & Story Synchronizer

A Python script to automatically create and link Epics, Stories, and Tasks in JIRA
based on a simple CSV file.

## Setup

```bash
set JIRA_URL=your_link
set JIRA_TOKEN=your_personal_access_token
```

## Usage
```bash
python jira_sync.py <PROJECT_KEY> <CSV_FILENAME>
```

## Features
- ✅ Creates missing **Epics**, **Stories**, and **Tasks**
- 🔗 Ensures **Story / Task → Epic** links are correct
- 🧩 Automatically detects Epic Link field ID
- 🧠 Avoids duplicate creation (checks existing issues)
- 🪵 Logs all actions (Created, Updated, No Change) to a structured CSV file