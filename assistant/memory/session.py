from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

from assistant.memory.schema import MemoryEntry, MemoryType
from assistant.memory.store import MemoryStore
from assistant.config import settings

if TYPE_CHECKING:
    from assistant.llm.client import LMStudioClient


class SourceRef(TypedDict):
    """Structured reference to a RAG source for UI transparency display."""

    text: str
    source: str
    score: float
    type: str  # "session" | "knowledge"


class SessionMemory:
    """
    Manages in-session conversation buffer and RAG memory persistence.

    Responsibilities:
    - Buffer the current conversation turns in RAM.
    - Inject relevant past memories into each LLM prompt.
    - Persist end-of-session summary to ChromaDB via MemoryStore.
    - Allow the LLM to record explicit progress / weak topics.
    """

    def __init__(self, store: MemoryStore) -> None:
        self._store = store
        self._current_turns: list[dict[str, str]] = []

    # ------------------------------------------------------------------
    # In-session buffer
    # ------------------------------------------------------------------

    def add_turn(self, role: str, content: str) -> None:
        self._current_turns.append({"role": role, "content": content})

    def clear_turns(self) -> None:
        self._current_turns.clear()

    # ------------------------------------------------------------------
    # Memory injection
    # ------------------------------------------------------------------

    def get_relevant_context(self, query: str) -> str:
        """Return formatted past-session memories relevant to *query*."""
        context, _ = self.get_relevant_context_with_sources(query)
        return context

    def get_relevant_context_with_sources(self, query: str) -> tuple[str, list[SourceRef]]:
        """Return formatted context string AND structured source list for UI display."""
        mem_items = self._store.query_with_metadata(query, n_results=settings.max_context_memories)
        kb_items = self._store.query_knowledge_with_metadata(
            query, n_results=settings.max_knowledge_context_chunks
        )

        sources: list[SourceRef] = [
            SourceRef(
                text=m["text"][:200],
                source=m["source"],
                score=m["score"],
                type=m["type"],
            )
            for m in mem_items
        ] + [
            SourceRef(
                text=k["text"][:200],
                source=k["source"],
                score=k["score"],
                type=k["type"],
            )
            for k in kb_items
        ]

        if not mem_items and not kb_items:
            return "", sources

        lines: list[str] = []
        if mem_items:
            lines.append("📚 Контекст из прошлых сессий:")
            for i, mem in enumerate(mem_items, start=1):
                lines.append(f"  {i}. {mem['text']}")

        if kb_items:
            lines.append("🧭 Проверенные факты из базы знаний:")
            for i, fact in enumerate(kb_items, start=1):
                lines.append(f"  {i}. {fact['text']}")

        return "\n".join(lines), sources

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------

    async def save_session(self, llm: "LMStudioClient") -> str:
        """Summarise the current session and store it permanently."""
        if len(self._current_turns) < 2:
            return "Недостаточно диалога для сохранения."

        conversation = "\n".join(
            f"{t['role'].upper()}: {t['content']}" for t in self._current_turns
        )

        summary = await llm.summarize(conversation)

        entry = MemoryEntry(
            type=MemoryType.SESSION,
            content=summary,
            metadata={
                "turn_count": len(self._current_turns),
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            },
        )
        self._store.add(entry)
        self.clear_turns()
        return f"✅ Сессия сохранена: {summary[:120]}…"

    # ------------------------------------------------------------------
    # Explicit progress / weak topic recording (called by LLM tools)
    # ------------------------------------------------------------------

    def record_progress(self, topic: str, status: str) -> str:
        entry = MemoryEntry(
            type=MemoryType.PROGRESS,
            content=(
                f"[{datetime.now().strftime('%Y-%m-%d')}] "
                f"Тема: {topic} | Статус: {status}"
            ),
            metadata={"topic": topic, "status": status},
        )
        self._store.add(entry)
        return f"✅ Прогресс зафиксирован: {topic} — {status}"

    def record_weak_topic(self, topic: str, reason: str = "") -> str:
        content = f"⚠️ Слабое место: {topic}"
        if reason:
            content += f" — {reason}"
        entry = MemoryEntry(
            type=MemoryType.WEAK_TOPIC,
            content=content,
            metadata={"topic": topic},
        )
        self._store.add(entry)
        return f"📌 Слабое место зафиксировано: {topic}"

    # ------------------------------------------------------------------
    # Progress overview
    # ------------------------------------------------------------------

    def get_progress_summary(self) -> str:
        docs = self._store.get_by_type(
            MemoryType.PROGRESS, MemoryType.WEAK_TOPIC, MemoryType.ACHIEVEMENT
        )
        if not docs:
            return "Прогресс пока не зафиксирован.\nНачни первую сессию — и данные появятся здесь."
        # Show latest 30 entries
        return "\n".join(docs[-30:])
