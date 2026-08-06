# ML Interview Assistant

An AI assistant for LM/MLOps/DevOps interview preparation featuring two operating modes:

- A Streamlit web interface for interactive chat, fact-checking, and coding tasks.
- A voice-enabled CLI interface (Push-to-Talk) for a browser-free voice interaction workflow.

The project implements:

- Local LLM support via LM Studio (OpenAI-compatible API),
- RAG based on a knowledge base and past sessions (ChromaDB),
- Tools for tracking progress, taking notes, managing tasks, and performing web searches,
- Fact-checking of the latest response using Tavily + LLM critique.

## Features

- 3 coaching modes: Exploration, Diagnosis, Interview.
- Voice input in CLI (hold 'X' key) and web interface (microphone button).
- RAG context derived from:
- extensive memory of past sessions,
- a local knowledge corpus (`KNOWLEDGE_RAG_MLOPS_LMOPS.md`).
- Fact-checking (Verify) with verdict output: ACCURATE / INACCURATE / REQUIRES VERIFICATION.
- Integrated UI code features:
- editing `practice.py`,
- quick syntax checking,
- code execution in a sandbox script.
# ML Interview Assistant

An AI assistant for LM/MLOps/DevOps interview preparation with two interfaces:

- A Streamlit web interface for interactive chat, fact-checking, and coding practice.
- A voice-enabled CLI interface (Push-to-Talk) for a browser-free workflow. This project combines:

- a local LLM via LM Studio (OpenAI-compatible API),
- RAG based on a knowledge base and past sessions (ChromaDB),
- tools for tracking progress, taking notes, managing practical tasks, and web searching,
- final fact-checking via Tavily + LLM critique.

## Features

- 3 coaching modes: Exploration, Diagnosis, Interview.
- Voice input in CLI (hold the `X` key) and web interface (microphone button).
- RAG context usage based on:
- long-term memory of previous sessions,
- local knowledge base `KNOWLEDGE_RAG_MLOPS_LMOPS.md`.
- Verification tab with verdicts: ACCURATE, INACCURATE, NEEDS VERIFICATION.
- Built-in "Code" tab in the interface:
- editing the `practice.py` file,
- quick syntax check,
- code execution in a temporary sandbox script.
- Export current session to Markdown/PDF and import chat from `.md`/`.json` files.
- Automatic chat session saving to vector memory.

## Tech Stack

- Python 3.10+
- Streamlit
- OpenAI SDK (connecting to LM Studio)
- ChromaDB + sentence-transformers
- faster-whisper (STT — speech-to-text)
- Tavily API (web search)

## Project Structure

```text
.
├─ app.py                              # Entry point for the Streamlit interface
├─ main.py                             # Entry point for the voice CLI
├─ requirements.txt
├─ assistant/
│  ├─ config.py                        # Settings based on .env
│  ├─ core/assistant.py                # Dialogue, tool, and mode management
│  ├─ llm/client.py                    # Client for LM Studio
│  ├─ memory/                          # Data schemas and ChromaDB storage
│  ├─ knowledge/ingest.py              # Loading the knowledge base into Chroma
│  ├─ tools/                           # Web search, notes, practice files, export
│  ├─ ui/                              # Streamlit UI components
│  └─ voice/stt.py                     # Speech-to-Text (STT)
├─ notes/                              # Markdown notes
├─ study_notes.txt                     # Session notes log
├─ practice.py                         # File containing practice exercises
├─ _solutions/                         # Hidden reference solutions
└─ memory_db/                          # Local vector database (Chroma)
```

## Quick Start

### 1) Cloning and Environment Setup

```powershell
git clone <repo_url>
cd "AI Assistent WorkUp"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Configuring `.env`

Create or update the `.env` file in the project root directory.

### 3) Launching LM Studio

1. Launch LM Studio locally.
2. Load a chat model and an embedding model.
3. Start the local server compatible with the OpenAI API (usually `http://localhost:1234/v1`). ### 4) (Optional) Loading the knowledge base

```powershell
python -m assistant.knowledge.ingest
```

If you skip this step, the assistant will still function, but without full-fledged knowledge fragment search capabilities (RAG).

## Launching the application

### Web interface

```powershell
streamlit run app.py
```

Once launched, open the URL displayed in the terminal (usually `http://localhost:8501`). ### Voice interface (CLI)

```powershell
python main.py
```

Controls:

- Hold `X` to record.
- Release `X` to send speech to the assistant.
- Press `Ctrl+C` to stop and save the session.

Russian spoken commands for mode switching:

- "режим интервью"
- "режим диагностики"
- "режим обучения"
- "статус режима"
- "помощь"

## Coaching Modes

- `study`: step-by-step learning with explanations.
- `diagnostic`: quick gap analysis and weak-topic detection.
- `interview`: mock interview simulation (with timer in UI).

## Main Chat Commands

- `/mode study`
- `/mode diagnostic`
- `/mode interview`
- `/mode status`
- `/help`

## Export and Import

In the sidebar you can:

- export progress/notes/chat to Markdown,
- export to PDF (if `fpdf2` is installed),
- import chat from `.md` or `.json` and continue the session.

## Fact Checking

In the Verify tab:

1. The latest assistant response is selected.
2. Web search is executed.
3. A second-pass LLM critique is performed.
4. A short fact-check report and final verdict are shown.

## Common Issues

- `TAVILY_API_KEY is not configured`
  - Add a valid key to `.env`.

- LM Studio connection error
  - Verify `LM_STUDIO_BASE_URL`.
  - Make sure the LM Studio local server is running.

- Slow or inaccurate transcription
  - Tune `WHISPER_MODEL` for your hardware (for example, `medium` vs `large-v3-turbo`).

- PDF export is unavailable
  - Install: `pip install fpdf2`.

## Useful Files

- `app.py` - Web UI entry point
- `main.py` - Voice CLI entry point
- `assistant/config.py` - central configuration
- `assistant/knowledge/ingest.py` - knowledge collection ingestion
- `assistant/memory/store.py` - session and knowledge vector memory layers
- `assistant/tools/export.py` - export/import logic
