# Telegram Intelligence Brief Generator (n8n Edition)

Internal documentation for the Gemini-powered intelligence pipeline.

## System Architecture

The pipeline is an automated ETL (Extract, Transform, Load) and Analysis workflow orchestrated by **n8n**. It transforms raw Telegram message streams into executive-level geopolitical briefs.

### 1. Extraction & Transfer
- **Trigger:** n8n Schedule Trigger (every 4 hours).
- **Extraction:** AWS Lambda (`TG_NewsSender`) fetches raw data.
- **Transfer:** n8n SSH node uploads `messages.json` to a Linux production server.

### 2. Transformation (`process_messages.py`)
- **Cleaning:** Removes emojis, Telegram links, and excessive whitespace.
- **Filtering:** Filters messages by length (>100 chars) and excludes specific regions/promotional noise.
- **Structuring:** Identifies groups, parses timestamps into ISO format, and calculates the reporting duration.

### 3. Analysis & Generation (`instructions.txt`)
- **Prompting:** Merges `instructions.txt` with `messages_processed.json`.
- **Guidelines:** Strict adherence to active voice, deduplication, and thematic organization.
- **Citations:** Every key fact is cited inline using `<sup>[Group Name, HH:MM]</sup>`.
- **Execution:** The `gemini` CLI tool processes the prompt and outputs raw HTML.

### 4. Finalization
- **Cleanup:** All temporary files (`messages.json`, `messages_processed.json`, `combined_prompt.txt`) and the `brief.html` artifact are deleted after the workflow concludes (e.g., after the brief is emailed).

## File Registry

| File | Role |
| :--- | :--- |
| `TG_News.json` | The n8n workflow configuration. |
| `process_messages.py` | Python 3 processing logic. |
| `instructions.txt` | The intelligence analyst system prompt. |
| `README.md` | General project documentation and setup. |
| `GEMINI.md` | Technical pipeline overview (this file). |

## Repository
Managed at: [https://github.com/mclancyfl21/tgn8nnews](https://github.com/mclancyfl21/tgn8nnews)