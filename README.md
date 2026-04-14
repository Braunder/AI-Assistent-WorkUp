# ML Interview Assistant

AI-ассистент для подготовки к собеседованиям по LM/MLOps/DevOps с двумя режимами работы:

- Streamlit Web UI для интерактивного чата, проверки фактов и работы с кодом.
- Voice CLI (push-to-talk) для голосового сценария без браузера.

Проект объединяет:

- локальную LLM через LM Studio (OpenAI-compatible API),
- RAG по базе знаний и прошлым сессиям (ChromaDB),
- инструменты записи прогресса, заметок, задач и web-поиска,
- fact-check последнего ответа через Tavily + LLM critique.

## Возможности

- 3 режима коучинга: Study, Diagnostic, Interview.
- Голосовой ввод в CLI (удержание клавиши `X`) и в Web UI (кнопка микрофона).
- RAG-контекст из:
  - долгосрочной памяти прошлых сессий,
  - локального корпуса знаний `KNOWLEDGE_RAG_MLOPS_LMOPS.md`.
- Проверка фактов (Verify) с выводом вердикта: ТОЧНЫЙ / НЕТОЧНЫЙ / ТРЕБУЕТ ПРОВЕРКИ.
- Встроенная вкладка Code в UI:
  - редактирование `practice.py`,
  - быстрая проверка синтаксиса,
  - запуск кода в sandbox-скрипте.
# ML Interview Assistant

An AI assistant for LM/MLOps/DevOps interview preparation with two interfaces:

- Streamlit Web UI for interactive chat, fact-checking, and code practice.
- Voice CLI (push-to-talk) for a browser-free workflow.

This project combines:

- a local LLM via LM Studio (OpenAI-compatible API),
- RAG over a knowledge base and past sessions (ChromaDB),
- tools for progress tracking, notes, practice tasks, and web search,
- final-answer fact-checking through Tavily + LLM critique.

## Features

- 3 coaching modes: Study, Diagnostic, Interview.
- Voice input in CLI (hold `X`) and in Web UI (microphone button).
- RAG context from:
  - long-term memory of previous sessions,
  - local knowledge corpus `KNOWLEDGE_RAG_MLOPS_LMOPS.md`.
- Verify tab with verdicts: ACCURATE / INACCURATE / NEEDS VERIFICATION.
- Built-in Code tab in UI:
  - edit `practice.py`,
  - run quick syntax checks,
  - execute code in a temporary sandbox script.
- Export current session to Markdown/PDF and import chat from `.md`/`.json`.
- Automatic chat-session persistence into vector memory.

## Tech Stack

- Python 3.10+
- Streamlit
- OpenAI SDK (connected to LM Studio)
- ChromaDB + sentence-transformers
- faster-whisper (STT)
- Tavily API (web search)

## Project Structure

```text
.
├─ app.py                              # Streamlit UI entry point
├─ main.py                             # Voice CLI entry point
├─ requirements.txt
├─ assistant/
│  ├─ config.py                        # .env-based settings
│  ├─ core/assistant.py                # Dialog orchestration, tools, modes
│  ├─ llm/client.py                    # LM Studio client
│  ├─ memory/                          # Schemas and ChromaDB store
│  ├─ knowledge/ingest.py              # Knowledge corpus ingestion into Chroma
│  ├─ tools/                           # Web search, notes, practice files, export
│  ├─ ui/                              # Streamlit UI components
│  └─ voice/stt.py                     # Speech-to-text
├─ notes/                              # Markdown notes
├─ study_notes.txt                     # Session notes log
├─ practice.py                         # User practice/tasks file
├─ _solutions/                         # Hidden reference solutions
└─ memory_db/                          # Local vector database (Chroma)
```

## Quick Start

### 1) Clone and create environment

```powershell
git clone <repo_url>
cd "AI Assistent WorkUp"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Configure `.env`

Create or update `.env` in the project root.

Example:

```env
TAVILY_API_KEY=your_tavily_api_key

LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=qwen3.5-9b
LM_STUDIO_EMBEDDING_MODEL=text-embedding-qwen3-embedding-0.6b

PRACTICE_FILE_PATH=practice.py
NOTES_FILE_PATH=study_notes.txt
MEMORY_DB_PATH=memory_db
KNOWLEDGE_CORPUS_PATH=KNOWLEDGE_RAG_MLOPS_LMOPS.md

MAX_CONTEXT_MEMORIES=5
MAX_KNOWLEDGE_CONTEXT_CHUNKS=6
WHISPER_MODEL=medium
AUTO_SAVE_EVERY_TURNS=2
AUTO_SAVE_MIN_INTERVAL_SEC=120
```

### 3) Start LM Studio

1. Run LM Studio locally.
2. Load a chat model and an embedding model.
3. Enable the local OpenAI-compatible server (usually `http://localhost:1234/v1`).

### 4) (Optional) Ingest the knowledge base

```powershell
python -m assistant.knowledge.ingest
```

If you skip ingestion, the assistant still works, but without full knowledge-chunk retrieval in RAG.

## Run the App

### Web UI

```powershell
streamlit run app.py
```

After startup, open the URL shown in terminal (usually `http://localhost:8501`).

### Voice CLI

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

## License

Add a license section (MIT/Apache-2.0/etc.) before publishing the repository.
