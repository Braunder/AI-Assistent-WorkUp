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
- Экспорт текущей сессии в Markdown/PDF и импорт диалога из `.md`/`.json`.
- Автосохранение истории сессии в векторную память.

## Технологии

- Python 3.10+
- Streamlit
- OpenAI SDK (подключение к LM Studio)
- ChromaDB + sentence-transformers
- faster-whisper (STT)
- Tavily API (web search)

## Структура проекта

```text
.
├─ app.py                              # Точка входа Streamlit UI
├─ main.py                             # Точка входа Voice CLI
├─ requirements.txt
├─ assistant/
│  ├─ config.py                        # Настройки через .env
│  ├─ core/assistant.py                # Оркестрация диалога, инструменты, режимы
│  ├─ llm/client.py                    # Клиент LM Studio
│  ├─ memory/                          # Схемы и ChromaDB store
│  ├─ knowledge/ingest.py              # Инжест корпуса знаний в Chroma
│  ├─ tools/                           # Web search, заметки, файлы практики, export
│  ├─ ui/                              # Streamlit интерфейс
│  └─ voice/stt.py                     # Speech-to-text
├─ notes/                              # Markdown-заметки
├─ study_notes.txt                     # Журнал заметок
├─ practice.py                         # Практика/задачи пользователя
├─ _solutions/                         # Эталонные решения задач
└─ memory_db/                          # Локальная векторная база (Chroma)
```

## Быстрый старт

### 1) Клонирование и окружение

```powershell
git clone <repo_url>
cd "AI Assistent WorkUp"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Настройка `.env`

Обнови файл `.env` в корне проекта.


### 3) Запуск LM Studio

1. Запусти LM Studio локально.
2. Загрузи chat-модель и embedding-модель.
3. Включи локальный OpenAI-compatible сервер (обычно `http://localhost:1234/v1`).

### 4) (Опционально) Инжест базы знаний

```powershell
python -m assistant.knowledge.ingest
```

Если не выполнить инжест, ассистент всё равно работает, но без полноценных knowledge-chunks в RAG.

## Запуск приложения

### Web UI

```powershell
streamlit run app.py
```

После запуска открой URL из терминала (обычно `http://localhost:8501`).

### Voice CLI

```powershell
python main.py
```

Управление:

- Удерживай `X` для записи.
- Отпусти `X` для отправки фразы в ассистент.
- `Ctrl+C` для завершения и сохранения сессии.

Голосовые команды для смены режима:

- «режим интервью»
- «режим диагностики»
- «режим обучения»
- «статус режима»
- «помощь»

## Режимы коучинга

- `study`: пошаговое обучение с пояснениями.
- `diagnostic`: быстрая проверка пробелов и слабых мест.
- `interview`: симуляция mock-интервью (в UI есть таймер).

## Основные команды в чате

- `/mode study`
- `/mode diagnostic`
- `/mode interview`
- `/mode status`
- `/help`

## Экспорт и импорт

В sidebar доступны:

- экспорт прогресса/заметок/диалога в Markdown,
- экспорт в PDF (если установлен `fpdf2`),
- импорт диалога из `.md` или `.json` для продолжения сессии.

## Проверка фактов

Во вкладке Verify:

1. Берется последний ответ ассистента.
2. Выполняется web-поиск.
3. Запускается второй проход LLM-критики.
4. Выводится короткий фактчек-отчет и вердикт.

## Типичные проблемы

- `TAVILY_API_KEY не настроен`
  - Добавь рабочий ключ в `.env`.

- Ошибка подключения к LM Studio
  - Проверь `LM_STUDIO_BASE_URL`.
  - Убедись, что локальный сервер LM Studio запущен.

- Медленная/неточная транскрибация
  - Подбери `WHISPER_MODEL` под железо (например, `medium` vs `large-v3-turbo`).

- Нет PDF-экспорта
  - Установи: `pip install fpdf2`.

## Полезные файлы

- `app.py` — вход в Web UI
- `main.py` — голосовой CLI
- `assistant/config.py` — все ключевые настройки
- `assistant/knowledge/ingest.py` — наполнение knowledge collection
- `assistant/memory/store.py` — Chroma-слои памяти и knowledge
- `assistant/tools/export.py` — логика экспорта/импорта
