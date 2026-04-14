import json
import re
from typing import Any, AsyncIterator

from assistant.config import settings
from assistant.core.prompts import build_system_prompt
from assistant.llm.client import LMStudioClient
from assistant.memory.schema import MemoryType
from assistant.memory.session import SessionMemory, SourceRef
from assistant.memory.store import MemoryStore
from assistant.tools.practice_file import (
    append_to_practice_file,
    read_practice_file,
    write_practice_file,
)
from assistant.tools.notes_file import append_note, read_notes_file
from assistant.tools.notes_dir import (
    append_note_file,
    list_note_files,
    read_note_file,
    write_note_file,
)
from assistant.tools.screen_capture import ScreenCaptureResult, capture_screen
from assistant.tools.solutions_file import read_solution, write_solution
from assistant.tools.web_search import search_web

# -------------------------------------------------------------------------
# OpenAI tool schemas (used both for format injection and dispatch)
# -------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Поиск актуальной информации в интернете через Tavily",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос на русском или английском"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_practice_file",
            "description": "Прочитать текущее содержимое файла practice.py",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_practice_file",
            "description": "Полностью перезаписать practice.py новым содержимым",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Полное содержимое файла"},
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_to_practice_file",
            "description": "Добавить новый код, задачу или пример в конец practice.py",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Код для добавления"},
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_progress",
            "description": (
                "Зафиксировать прогресс пользователя по теме в долгосрочную память. "
                "Вызывай только по явной просьбе пользователя (например, 'запомни', 'зафиксируй тему')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Название темы"},
                    "status": {
                        "type": "string",
                        "description": "Статус: 'изучено', 'в процессе', 'нужно повторить', или оценка",
                    },
                },
                "required": ["topic", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_weak_topic",
            "description": (
                "Зафиксировать слабое место пользователя. "
                "Вызывай только по явной просьбе пользователя или после его explicit подтверждения."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Тема или концепция"},
                    "reason": {"type": "string", "description": "Почему это слабое место (опционально)"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_notes_file",
            "description": "Прочитать журнал записей пользователя study_notes.txt",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_note",
            "description": "Добавить новую запись в журнал study_notes.txt",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Текст заметки: что изучили, что повторить, следующий шаг",
                    },
                    "title": {
                        "type": "string",
                        "description": "Короткий заголовок заметки",
                    },
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_note_files",
            "description": "Показать список заметок в папке notes/",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_note_file",
            "description": "Создать или перезаписать markdown заметку в папке notes/",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Название файла/заметки"},
                    "content": {"type": "string", "description": "Текст заметки"},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_note_file",
            "description": "Прочитать markdown заметку из папки notes/",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Имя файла заметки"},
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_note_file",
            "description": "Добавить новый блок в существующую заметку в папке notes/",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Имя файла заметки"},
                    "content": {"type": "string", "description": "Текст для добавления"},
                },
                "required": ["file_name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "capture_screen",
            "description": "Сделать снимок экрана и передать изображение мультимодальной модели для анализа",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_solution",
            "description": (
                "Сохранить эталонное решение задачи в скрытый файл (_solutions/task_N.py). "
                "Вызывай сразу после того как записал задачу-скелет в practice.py, "
                "чтобы потом можно было проверить ответ пользователя."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Номер или идентификатор задачи (например: '5')"},
                    "content": {"type": "string", "description": "Полный код правильного решения с тестами"},
                },
                "required": ["task_id", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_solution",
            "description": (
                "Прочитать эталонное решение из скрытого файла для проверки ответа пользователя. "
                "Никогда не показывай текст решения пользователю напрямую — используй только для сравнения."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Номер задачи"},
                },
                "required": ["task_id"],
            },
        },
    },
]

# -------------------------------------------------------------------------
# Qwen3 chat-template tool helpers
# -------------------------------------------------------------------------
_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*<function=([^>]+)>(.*?)</function>\s*</tool_call>",
    re.DOTALL,
)
_FUNCTION_CALL_RE = re.compile(r"<function=([^>]+)>(.*?)</function>", re.DOTALL)
_PARAM_RE = re.compile(r"<parameter=([^>]+)>\n?(.*?)\n?</parameter>", re.DOTALL)
_THINK_BLOCK_RE = re.compile(r"<think>.*?(</think>|$)", flags=re.IGNORECASE | re.DOTALL)
_THINK_CLOSE_RE = re.compile(r"</think>", flags=re.IGNORECASE)


def _format_tools_system_block() -> str:
    """Build the '# Tools' section injected at the top of the system prompt."""
    tool_jsons = "\n".join(json.dumps(t, ensure_ascii=False) for t in TOOLS)
    return (
        "# Tools\n\n"
        "You have access to the following functions:\n\n"
        f"<tools>\n{tool_jsons}\n</tools>\n\n"
        "If you choose to call a function ONLY reply in the following format with NO suffix:\n\n"
        "<tool_call>\n"
        "<function=example_function_name>\n"
        "<parameter=example_parameter_1>\n"
        "value_1\n"
        "</parameter>\n"
        "</function>\n"
        "</tool_call>\n\n"
        "<IMPORTANT>\n"
        "Reminder:\n"
        "- Function calls MUST follow the specified format\n"
        "- Required parameters MUST be specified\n"
        "- You may provide reasoning BEFORE the function call, but NOT after\n"
        "- If no function call is needed, answer the question normally\n"
        "</IMPORTANT>"
    )


def _parse_tool_calls(content: str) -> list[tuple[str, dict[str, Any]]]:
    """Extract all (function_name, args_dict) pairs from tool-call markup."""
    results: list[tuple[str, dict[str, Any]]] = []

    # Prefer strict parsing with <tool_call> wrappers.
    matches = list(_TOOL_CALL_RE.finditer(content))
    # Fallback for partially malformed output: parse bare <function=...> blocks.
    if not matches:
        matches = list(_FUNCTION_CALL_RE.finditer(content))

    for m in matches:
        name = m.group(1).strip()
        args: dict[str, Any] = {}
        for pm in _PARAM_RE.finditer(m.group(2)):
            args[pm.group(1).strip()] = pm.group(2).strip()
        results.append((name, args))
    return results


def _strip_tool_calls(content: str) -> str:
    """Remove tool-call markup from content, leaving only visible text."""
    cleaned = _TOOL_CALL_RE.sub("", content)
    cleaned = _FUNCTION_CALL_RE.sub("", cleaned)

    # During streaming we may see incomplete XML; hide it as soon as it starts.
    starts = [
        idx
        for idx in (
            cleaned.find("<tool_call>"),
            cleaned.find("<function="),
            cleaned.find("<parameter="),
        )
        if idx != -1
    ]
    if starts:
        cleaned = cleaned[: min(starts)]

    return cleaned.strip()


def _sanitize_assistant_text(content: str) -> str:
    """Remove tool-call and hidden reasoning markup from assistant text."""
    visible = _strip_tool_calls(content)
    visible = _THINK_BLOCK_RE.sub("", visible)
    visible = _THINK_CLOSE_RE.sub("", visible)
    return visible.strip()


def _format_tool_response(name: str, result: str) -> str:
    return f"<tool_response>\n{result}\n</tool_response>"


def _tool_result_to_message_part(name: str, result: Any) -> list[dict[str, Any]]:
    """Convert a tool result to multimodal user-message parts for the next model turn."""
    if isinstance(result, ScreenCaptureResult):
        image_url = f"data:{result.mime_type};base64,{result.image_base64}"
        text = (
            "<tool_response>\n"
            f"capture_screen: screenshot captured ({result.width}x{result.height}).\n"
            f"saved_path: {result.saved_path}\n"
            "Выполни визуальный анализ изображения и продолжай ответ.\n"
            "</tool_response>"
        )
        return [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

    return [{"type": "text", "text": _format_tool_response(name, str(result))}]


_MAX_TOOL_ITERATIONS = 6
_COACH_MODES = ("study", "diagnostic", "interview")
_CONFIDENCE_RE = re.compile(
    r"<confidence>(\d+)/5:\s*(.*?)</confidence>",
    re.IGNORECASE | re.DOTALL,
)


def _parse_confidence(text: str) -> tuple[str, dict[str, Any] | None]:
    """
    Extract the last <confidence>N/5: reason</confidence> tag from text.

    Returns:
        (cleaned_text, {score: int, reason: str} | None)
    """
    match = None
    for m in _CONFIDENCE_RE.finditer(text):
        match = m
    if match is None:
        return text, None
    score = max(1, min(5, int(match.group(1))))
    reason = match.group(2).strip()
    cleaned = _CONFIDENCE_RE.sub("", text).strip()
    return cleaned, {"score": score, "reason": reason}


class MLAssistant:
    """
    Central orchestrator.

    Manages:
    - Chat history (in-session, last 20 rounds for LLM context)
    - Tool-call loop (LLM calls tools ↔ results fed back until final text)
    - RAG memory injection (relevant past-session summaries in system prompt)
    - Progress / weak-topic recording via dedicated tools
    """

    def __init__(self) -> None:
        self._llm = LMStudioClient()
        self._store = MemoryStore()
        self._session = SessionMemory(self._store)
        # Rolling window of the current conversation for LLM context
        self._history: list[dict[str, Any]] = []
        self._coach_mode: str = "study"
        self._allow_next_step: bool = True
        # Populated after each chat turn — exposed to the Streamlit UI
        self.last_rag_sources: list[SourceRef] = []
        self.last_confidence: dict[str, Any] | None = None

    def _wants_next_step(self, user_input: str) -> bool:
        """Return True only when user explicitly asks to move forward in lesson flow."""
        text = user_input.strip().lower()
        if not text:
            return False

        stop_keywords = (
            "погоди",
            "подожди",
            "не тороп",
            "стоп",
            "останов",
            "не понял",
            "объясни",
            "подробнее",
        )
        if any(k in text for k in stop_keywords):
            return False

        next_keywords = (
            "дальше",
            "следующий шаг",
            "перейдем дальше",
            "переходи дальше",
            "продолжай",
            "next step",
            "go on",
        )
        if any(k in text for k in next_keywords):
            return True

        # First lesson turn may start with Step 1 without explicit "next".
        has_assistant_turns = any(msg.get("role") == "assistant" for msg in self._history)
        return not has_assistant_turns

    def _coach_mode_context(self) -> str:
        if self._coach_mode == "diagnostic":
            return (
                "Режим: diagnostic. Цель: быстро выявить пробелы. "
                "Работай короткими циклами: 1 вопрос -> ответ пользователя -> оценка уровня. "
                "После каждого ответа укажи: что верно, что неверно, и 1 следующий вопрос. "
                "Применяй mastery-gate: если есть ошибки или неуверенность, не меняй тему, "
                "а давай уточняющий вопрос до уверенного уровня владения (целевой порог 98%). "
                "Не задавай вопросы в стиле yes/no ('умеешь ли...'). "
                "Всегда проверяй знание через объяснение, мини-кейс или сравнение подходов."
            )
        if self._coach_mode == "interview":
            return (
                "Режим: interview. Веди себя как интервьюер LLM Engineer (production-oriented). "
                "Строй интервью от простого к сложному и не перескакивай между темами хаотично. "
                "Работай адаптивно: повышай сложность только при уверенно сильном ответе, "
                "при ошибках — сначала короткий разбор и контрольный follow-up на ту же тему. "
                "Используй mastery-gate: переход к новой теме только после того, как пользователь "
                "показал почти безошибочное понимание текущей темы (целевой порог 98%). "
                "Будь скептичным интервьюером: по умолчанию считай ответ неполным, пока не подтвержден деталями. "
                "Проверяй ответы перекрестно: задай минимум 2 follow-up вопроса разного типа "
                "(механизм, trade-off, edge-case, incident). "
                "Не используй yes/no-вопросы про навыки, используй только проверяемые вопросы по сути темы. "
                "После каждого ответа пользователя соблюдай формат фидбека: "
                "1) Верно (1-2 пункта), 2) Неточности/пробелы (конкретно), "
                "3) Как улучшить ответ за 60 секунд (структура), "
                "4) Оценка по рубрике (correctness/depth/tradeoffs/communication по 10-балльной шкале), "
                "5) Следующий вопрос (основной или уточняющий). "
                "Сильный упор делай на практику: latency/cost/throughput, RAG quality, "
                "eval design, incident debugging, guardrails и безопасность."
            )
        return (
            "Режим: study. Стандартный режим коучинга: объясняй кратко и структурно, "
            "только по одному шагу за сообщение. "
            "Не давай сразу длинный конспект, список тем и вопросы вместе. "
            "Сначала мини-объяснение, затем один вопрос/одно задание, затем жди ответ. "
            "Всегда двигайся от базовых концепций к продвинутым (simple -> intermediate -> advanced). "
            "Применяй mastery-gate: прежде чем перейти к новой теме, добейся устойчивого понимания "
            "текущей на уровне не ниже 98% (несколько точных ответов подряд без существенных ошибок). "
            "Не задавай лобовые вопросы про самооценку навыка ('умеешь ли ...'). "
            "Проверяй знание только через объяснение, применение и разбор ошибок."
            f"Переход к следующему шагу сейчас: {'РАЗРЕШЕН' if self._allow_next_step else 'ЗАПРЕЩЕН'}. "
            "Если переход ЗАПРЕЩЕН, не вводи новую тему и не выдавай новый шаг, "
            "а только объясняй/уточняй текущий шаг."
        )

    def _handle_local_command(self, user_input: str) -> str | None:
        """Process local slash commands without calling LLM."""
        text = user_input.strip()
        if not text.startswith("/"):
            return None

        lower = text.lower()
        if lower in ("/help", "/?"):
            return (
                "Команды:\n"
                "- /mode study\n"
                "- /mode diagnostic\n"
                "- /mode interview\n"
                "- /mode status"
            )

        if lower.startswith("/mode"):
            parts = lower.split()
            if len(parts) == 1 or parts[1] == "status":
                return f"Текущий режим: {self._coach_mode}"

            requested = parts[1]
            if requested not in _COACH_MODES:
                allowed = ", ".join(_COACH_MODES)
                return f"Неизвестный режим '{requested}'. Доступно: {allowed}."

            self._coach_mode = requested
            return f"Режим переключен: {self._coach_mode}"

        return "Неизвестная команда. Используй /help"

    def _auto_switch_mode(self, user_input: str) -> str | None:
        """Switch coaching mode from user intent and return switch notice if changed."""
        text = user_input.strip().lower()
        if not text or text.startswith("/"):
            return None

        interview_keywords = (
            "собесед",
            "интервью",
            "mock interview",
            "interview",
            "hr",
        )
        diagnostic_keywords = (
            "проверь",
            "протестируй",
            "квиз",
            "quiz",
            "оцен",
            "проверка",
        )
        study_keywords = (
            "объясни",
            "разбери",
            "обуч",
            "изуч",
            "теор",
            "план",
        )

        target_mode = self._coach_mode
        if any(k in text for k in interview_keywords):
            target_mode = "interview"
        elif any(k in text for k in diagnostic_keywords):
            target_mode = "diagnostic"
        elif any(k in text for k in study_keywords):
            target_mode = "study"

        if target_mode == self._coach_mode:
            return None

        previous = self._coach_mode
        self._coach_mode = target_mode
        return f"[auto-mode] {previous} -> {self._coach_mode}\n"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(self, user_input: str) -> tuple[str, bool]:
        """
        Process a user message end-to-end.

        Returns:
            (response_text, practice_file_changed)
        """
        local = self._handle_local_command(user_input)
        if local is not None:
            self._history.append({"role": "user", "content": user_input})
            self._history.append({"role": "assistant", "content": local})
            self._session.add_turn("user", user_input)
            self._session.add_turn("assistant", local)
            return local, False

        if self._coach_mode == "study":
            self._allow_next_step = self._wants_next_step(user_input)

        mode_notice = self._auto_switch_mode(user_input)

        memory_ctx, rag_sources = self._session.get_relevant_context_with_sources(user_input)
        self.last_rag_sources = rag_sources
        base_prompt = build_system_prompt(memory_ctx, self._coach_mode_context())
        system_prompt = _format_tools_system_block() + "\n\n" + base_prompt

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *self._history[-20:],  # last 20 turns for rolling context
            {"role": "user", "content": user_input},
        ]

        raw_text, practice_changed = await self._run_tool_loop(messages, _MAX_TOOL_ITERATIONS)
        text, confidence = _parse_confidence(raw_text)
        self.last_confidence = confidence
        if mode_notice:
            text = mode_notice + text
        self._history.append({"role": "user", "content": user_input})
        self._history.append({"role": "assistant", "content": text})
        self._session.add_turn("user", user_input)
        self._session.add_turn("assistant", text)
        return text, practice_changed

    async def _run_tool_loop(
        self,
        messages: list[dict[str, Any]],
        remaining_iterations: int,
    ) -> tuple[str, bool]:
        """Run assistant/tool turns until final non-tool text is produced."""
        practice_changed = False
        last_visible = ""

        for _ in range(max(0, remaining_iterations)):
            content = await self._llm.chat(messages)
            tool_calls = _parse_tool_calls(content)

            if not tool_calls:
                return _sanitize_assistant_text(content), practice_changed

            messages.append({"role": "assistant", "content": content})
            last_visible = _sanitize_assistant_text(content)

            response_parts: list[str] = []
            response_content_parts: list[dict[str, Any]] = []
            for fn_name, fn_args in tool_calls:
                tool_result = self._dispatch_tool(fn_name, fn_args)
                if fn_name in ("write_practice_file", "append_to_practice_file"):
                    practice_changed = True
                response_parts.append(_format_tool_response(fn_name, str(tool_result)))
                response_content_parts.extend(_tool_result_to_message_part(fn_name, tool_result))

            if response_content_parts:
                messages.append({"role": "user", "content": response_content_parts})
            else:
                messages.append({"role": "user", "content": "\n".join(response_parts)})

        # Limit reached — return last visible text the model produced (may be empty)
        fallback = last_visible if last_visible else "Не удалось получить финальный ответ."
        return fallback, practice_changed

    async def save_session(self) -> str:
        return await self._session.save_session(self._llm)

    def get_progress(self) -> str:
        return self._session.get_progress_summary()

    async def stream_chat(self, user_input: str) -> AsyncIterator[str]:
        """
        Stream assistant response token-by-token when possible.

        For prompts likely requiring tools, falls back to the full tool-enabled
        pipeline and yields the final text once.
        """
        local = self._handle_local_command(user_input)
        if local is not None:
            self._history.append({"role": "user", "content": user_input})
            self._history.append({"role": "assistant", "content": local})
            self._session.add_turn("user", user_input)
            self._session.add_turn("assistant", local)
            yield local
            return

        if self._coach_mode == "study":
            self._allow_next_step = self._wants_next_step(user_input)

        mode_notice = self._auto_switch_mode(user_input)
        if mode_notice:
            yield mode_notice

        memory_ctx, rag_sources = self._session.get_relevant_context_with_sources(user_input)
        self.last_rag_sources = rag_sources
        base_prompt = build_system_prompt(memory_ctx, self._coach_mode_context())
        system_prompt = _format_tools_system_block() + "\n\n" + base_prompt

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *self._history[-20:],
            {"role": "user", "content": user_input},
        ]

        chunks: list[str] = []
        shown_text = ""
        async for piece in self._llm.stream_chat(messages):
            chunks.append(piece)

            raw = "".join(chunks)
            visible = _sanitize_assistant_text(raw)
            if visible.startswith(shown_text):
                delta = visible[len(shown_text):]
            else:
                delta = visible
                shown_text = ""

            if delta:
                shown_text += delta
                yield delta

        first_pass_raw = "".join(chunks).strip()
        if not first_pass_raw:
            # Provider may not support streaming in current setup.
            text, _ = await self.chat(user_input)
            yield text
            return

        # Normalize model outputs that miss closing wrappers around tool calls.
        if "<function=" in first_pass_raw and "</tool_call>" not in first_pass_raw:
            first_pass_raw = first_pass_raw.replace("</function>", "</function>\n</tool_call>")

        first_pass_calls = _parse_tool_calls(first_pass_raw)
        final_text = _sanitize_assistant_text(first_pass_raw)
        practice_changed = False

        if first_pass_calls:
            messages.append({"role": "assistant", "content": first_pass_raw})
            response_parts: list[str] = []
            response_content_parts: list[dict[str, Any]] = []
            for fn_name, fn_args in first_pass_calls:
                tool_result = self._dispatch_tool(fn_name, fn_args)
                if fn_name in ("write_practice_file", "append_to_practice_file"):
                    practice_changed = True
                response_parts.append(_format_tool_response(fn_name, str(tool_result)))
                response_content_parts.extend(_tool_result_to_message_part(fn_name, tool_result))
            if response_content_parts:
                messages.append({"role": "user", "content": response_content_parts})
            else:
                messages.append({"role": "user", "content": "\n".join(response_parts)})

            tail_text, tail_changed = await self._run_tool_loop(messages, _MAX_TOOL_ITERATIONS - 1)
            practice_changed = practice_changed or tail_changed
            final_text = tail_text

            # Strip confidence tags emitted after tool round; update delta correctly
            final_text, _ = _parse_confidence(final_text)

            if final_text.startswith(shown_text):
                delta = final_text[len(shown_text):]
            else:
                delta = final_text
            if delta:
                yield delta

        # Parse & strip confidence from the complete response before storing
        final_text, confidence = _parse_confidence(final_text)
        self.last_confidence = confidence
        self._history.append({"role": "user", "content": user_input})
        self._history.append({"role": "assistant", "content": final_text})
        self._session.add_turn("user", user_input)
        self._session.add_turn("assistant", final_text)

    # ------------------------------------------------------------------
    # Hallucination detection & session overview
    # ------------------------------------------------------------------

    async def verify_claim(self, claim: str) -> str:
        """
        Verify a factual claim via web search + LLM critique pass.

        Returns a formatted fact-check report for the UI Verify tab.
        """
        from assistant.tools.web_search import search_web

        # Tavily API limits query to 400 characters
        search_query = claim[:400] if len(claim) > 400 else claim
        web_result = search_web(search_query, max_results=3)
        return await self._llm.critique_response(
            question=claim,
            answer=claim,
            web_facts=web_result,
        )

    def get_session_history(self) -> list[str]:
        """Return all stored session summaries for the history dashboard."""
        return self._store.get_by_type(MemoryType.SESSION)

    def get_progress_items(self) -> list[str]:
        """Return all stored progress records for visualization."""
        return self._store.get_by_type(MemoryType.PROGRESS)

    def get_weak_topics(self) -> list[str]:
        """Return all stored weak topic records."""
        return self._store.get_by_type(MemoryType.WEAK_TOPIC)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _requires_tools(user_input: str) -> bool:
        text = user_input.lower()
        keywords = (
            "поиск",
            "интернет",
            "найди",
            "search",
            "tavily",
            "practice.py",
            "запиши",
            "сохрани",
            "заметк",
            "конспект",
            "файл",
            "<tool_call>",
            "read_practice_file",
            "write_practice_file",
            "append_to_practice_file",
            "read_notes_file",
            "append_note",
        )
        return any(k in text for k in keywords)

    def _dispatch_tool(self, name: str, args: dict[str, Any]) -> str:
        try:
            match name:
                case "search_web":
                    return search_web(**args)
                case "read_practice_file":
                    return read_practice_file()
                case "write_practice_file":
                    return write_practice_file(**args)
                case "append_to_practice_file":
                    return append_to_practice_file(**args)
                case "record_progress":
                    return self._session.record_progress(**args)
                case "record_weak_topic":
                    return self._session.record_weak_topic(**args)
                case "read_notes_file":
                    return read_notes_file()
                case "append_note":
                    return append_note(**args)
                case "list_note_files":
                    return list_note_files()
                case "write_note_file":
                    return write_note_file(**args)
                case "read_note_file":
                    return read_note_file(**args)
                case "append_note_file":
                    return append_note_file(**args)
                case "capture_screen":
                    return capture_screen()
                case "write_solution":
                    return write_solution(**args)
                case "read_solution":
                    return read_solution(**args)
                case _:
                    return f"❌ Неизвестный инструмент: {name}"
        except Exception as exc:  # noqa: BLE001
            return f"❌ Ошибка при вызове {name}: {exc}"
