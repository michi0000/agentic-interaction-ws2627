# Agentic Interaction WS26/27 – Exercise

A simple Python agent that answers questions about calendar data using tool calls and a mock calendar API.

## Requirements

- Python 3.11+
- Internet connection
- OpenAI-compatible endpoint (default: Groq)

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```
## Dependencies

```text
openai
python-dotenv
requests
```
## Configuration

Create a `.env` file in the project root containing:

- OPENAI_BASE_URL
- MODEL
- OPENAI_API_KEY
- DATA_BASE_URL

Environment variables override values from `.env`.

## Run

From the repository root:

```bash
python -m agent "What is on my calendar on 2026-11-02?"
```

## How It Works

1. Receive a user question.
2. Send the question and tool definitions to the model.
3. The model decides whether a tool call is required.
4. The `get_calendar()` tool retrieves data from the calendar API.
5. The tool result is sent back to the model.
6. The model generates the final answer.

## Tools

### get_calendar(date)

Reads all appointments for a specific day.

Example:

```python
get_calendar("2026-11-02")
```

API endpoint:

```text
{DATA_BASE_URL}/calendar/YYYY-MM-DD.json
```


## Logging

Logs are written to:

```text
logs/"RUN-ID".log
```

Logged events:

- `user_task`
- `tool_call`
- `tool_result`
- `final`
- `error`

