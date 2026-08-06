from typing import Any, AsyncIterator
import re

from openai import AsyncOpenAI

from assistant.config import settings


_THINK_BLOCK_RE = re.compile(r"<think>.*?(</think>|$)", flags=re.IGNORECASE | re.DOTALL)
_THINK_CLOSE_RE = re.compile(r"</think>", flags=re.IGNORECASE)


def _strip_think_sections(text: str) -> str:
    cleaned = _THINK_BLOCK_RE.sub("", text)
    return _THINK_CLOSE_RE.sub("", cleaned).strip()


class LMStudioClient:
    """Async OpenAI-compatible client pointing at LM Studio."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=settings.lm_studio_base_url,
            api_key="lm-studio",  # LM Studio ignores the key, but the SDK requires one
        )
        self.model = settings.lm_studio_model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
    ) -> str:
        """Single API call, returns the assistant message content as plain text."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=4000,
        )
        return response.choices[0].message.content or ""

    async def summarize(self, conversation_text: str) -> str:
        """Produces a short summary for memory storage."""
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты суммаризатор. Создай краткое резюме (3-5 предложений) "
                    "разговора на русском языке, сохранив ключевые факты: "
                    "пройденные темы, ошибки пользователя, что нужно повторить."
                ),
            },
            {"role": "user", "content": conversation_text},
        ]
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content or ""
        return _strip_think_sections(raw)

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Yield assistant text deltas from LM Studio as they are generated."""
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
            max_tokens=4000,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None)
            if not piece:
                continue

            if isinstance(piece, str):
                yield piece
                continue

            # Some providers may return structured segments instead of plain text.
            if isinstance(piece, list):
                text = ""
                for part in piece:
                    if isinstance(part, dict):
                        text += str(part.get("text", ""))
                    else:
                        text += str(getattr(part, "text", ""))
                if text:
                    yield text

    async def critique_response(
        self,
        question: str,
        answer: str,
        web_facts: str,
    ) -> str:
        """
        Second-pass LLM critique for hallucination detection.

        Compares the assistant's answer against web search results and returns
        a structured fact-check report.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — критик и фактчекер. Твоя задача — найти фактические ошибки "
                    "в ответе ИИ, сравнивая его с данными из веб-поиска.\n"
                    "Отвечай строго на русском языке. Будь краток: максимум 5 пунктов.\n"
                    "Используй формат:\n"
                    "✅ <верный факт>\n"
                    "❌ <ошибочный факт: что правильно>\n"
                    "⚠️ <спорный / нет данных для проверки>\n\n"
                    "В конце добавь одну строку с вердиктом:\n"
                    "ВЕРДИКТ: ТОЧНЫЙ / НЕТОЧНЫЙ / ТРЕБУЕТ ПРОВЕРКИ"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Утверждение для проверки:\n{question}\n\n"
                    f"Ответ ИИ:\n{answer}\n\n"
                    f"Данные из веб-поиска:\n{web_facts}"
                ),
            },
        ]
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content or ""
        return _strip_think_sections(raw)
