# mcp-pronotes

**MCP server for Pronote -- access French school data from any AI assistant.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

The first [Model Context Protocol](https://modelcontextprotocol.io/) server for
[Pronote](https://www.index-education.com/fr/logiciel-gestion-vie-scolaire.php)
(by Index Education), the #1 school management platform in France used by
millions of students and parents. Connect any MCP-compatible AI assistant to your
child's school data: grades, timetables, homework, absences, averages, and
canteen menus.

## Features

| Tool | Description |
|------|-------------|
| `get_timetable` | Daily or weekly class schedule (lessons, rooms, teachers, cancellations) |
| `get_grades` | Grades with class average, min, max, and coefficient per subject |
| `get_homework` | Upcoming homework with due dates, completion status, and attached files or links |
| `get_absences` | Absences, delays, and punishments for a given period |
| `get_student_info` | Student profile, class, school name, and available periods |
| `get_averages` | Subject averages with student, class, min, and max values |
| `get_menus` | School canteen menus for a date range |

All tools support **multi-child accounts**: pass `child_name` to select a
specific child, or omit it to default to the first child.

## Quick start

### 1. Install dependencies

```bash
pip install pronotepy "mcp>=1.20.0"
```

Or from the requirements file:

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

Create a `config.json` in the project directory:

```json
{
  "pronote_url": "https://XXXX.index-education.net/pronote/mobile.parent.html",
  "username": "your_username",
  "password": "your_password",
  "account_type": "parent",
  "ent": "agora06",
  "device_name": "mcp-pronotes"
}
```

Set `account_type` to `"student"` if you are logging in with a student account.

Alternatively, create a `.env` file next to `server.py`, or export the same
environment variables. Process environment variables take precedence over
`.env` and `config.json`:

```dotenv
PRONOTE_URL=https://XXXX.index-education.net/pronote/mobile.parent.html
PRONOTE_USERNAME=your_username
PRONOTE_PASSWORD=your_password
PRONOTE_ACCOUNT_TYPE=parent
PRONOTE_ENT=agora06
PRONOTE_DEVICE_NAME=mcp-pronotes
```

### 3. Register with Claude Code

```bash
claude mcp add pronotes -- python /path/to/mcp-pronotes/server.py
```

Or with environment variables instead of config.json:

```bash
claude mcp add pronotes \
  -e PRONOTE_URL="https://XXXX.index-education.net/pronote/..." \
  -e PRONOTE_USERNAME="your_username" \
  -e PRONOTE_PASSWORD="your_password" \
  -- python /path/to/mcp-pronotes/server.py
```

The server communicates over stdio and works with any MCP-compatible client.

## Configuration

The server reads configuration from `config.json`, `.env`, and the process
environment. Process environment variables have the highest priority.

| Source | Key | Description |
|--------|-----|-------------|
| config.json | `pronote_url` | Full Pronote URL for your school |
| config.json | `username` | Your Pronote username |
| config.json | `password` | Your Pronote password |
| config.json | `account_type` | `"parent"` or `"student"` |
| config.json | `ent` | ENT provider; use `"agora06"` for Agora06/EduConnect |
| config.json | `account_pin` | Optional Pronote MFA PIN |
| config.json | `device_name` | Remembered-device label |
| config.json | `client_identifier` | Optional explicit remembered-device identifier |
| env var | `PRONOTE_URL` | Overrides `pronote_url` |
| env var | `PRONOTE_USERNAME` | Overrides `username` |
| env var | `PRONOTE_PASSWORD` | Overrides `password` |
| env var | `PRONOTE_ACCOUNT_TYPE` | Overrides `account_type` |
| env var | `PRONOTE_ENT` | ENT provider; use `agora06` for Agora06/EduConnect |
| env var | `PRONOTE_ACCOUNT_PIN` | Optional Pronote MFA PIN |
| env var | `PRONOTE_DEVICE_NAME` | Remembered-device label; defaults to `mcp-pronotes` |
| env var | `PRONOTE_CLIENT_IDENTIFIER` | Optional explicit remembered-device identifier |

## Multi-child support

If you are a parent with multiple children on the same Pronote account, every
tool accepts an optional `child_name` parameter. Pass the child's full name as
it appears in Pronote. When omitted, the server defaults to the first child.

Use the `get_student_info` tool to list all children and their classes.

## Authentication

The server authenticates with a standard Pronote username and password. This is
the same login you use on the Pronote website or mobile app.

**ENT (Espace Numerique de Travail):** Set `PRONOTE_ENT=agora06` for an Agora06
parent or student account. The server selects the matching EduConnect profile
automatically. It stores Pronote's generated device identifier in the ignored
`.pronote-state.json` file so subsequent connections reuse the registered
device. If Pronote asks for a PIN, set `PRONOTE_ACCOUNT_PIN` for the first
connection and remove it afterwards.

**QR code login:** Not yet supported. QR code / token-based authentication is
planned for a future release.

## Session management

Pronote sessions expire after approximately 30 minutes. The server handles this
automatically: it caches the session for 25 minutes and reconnects transparently
when needed. No manual intervention required.

## Requirements

- Python 3.10+
- [pronotepy](https://github.com/bain3/pronotepy) >= 2.14.0
- [mcp](https://pypi.org/project/mcp/) >= 1.20.0

## Credits

Built with [pronotepy](https://github.com/bain3/pronotepy) by bain3.

## License

[MIT](LICENSE) -- Copyright 2026 HAL-XP
