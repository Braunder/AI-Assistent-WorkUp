from __future__ import annotations

from collections.abc import AsyncIterator
from collections import OrderedDict
import logging
import re
import httpx
from urllib.parse import urlparse, urlunparse


logger = logging.getLogger(__name__)


_CODE_BLOCK_RE = re.compile(r"```.*?```", flags=re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
_TAG_RE = re.compile(r"</?[^>]+>")
_MULTI_PUNCT_RE = re.compile(r"([!?.,:;])\1+")


class TTSEngine:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        voice: str,
        language: str,
        instruct: str,
        do_sample: bool,
        temperature: float,
        top_p: float,
        top_k: int,
        repetition_penalty: float,
        max_new_tokens: int,
        use_streaming: bool,
        stream_sample_rate: int,
        cache_enabled: bool,
        cache_max_items: int,
        cache_max_text_len: int,
        cache_chunk_bytes: int,
        stream_emit_chunk_bytes: int,
        max_input_chars: int,
        min_chunk_chars: int,
    ) -> None:
        self._base_url = self._normalize_base_url(base_url)
        self._voice = voice
        self._language = language
        self._instruct = instruct
        self._do_sample = do_sample
        self._temperature = temperature
        self._top_p = top_p
        self._top_k = top_k
        self._repetition_penalty = repetition_penalty
        self._max_new_tokens = max_new_tokens
        self._use_streaming = use_streaming
        self._stream_sample_rate = stream_sample_rate
        self._cache_enabled = cache_enabled
        self._cache_max_items = max(1, cache_max_items)
        self._cache_max_text_len = max(1, cache_max_text_len)
        self._cache_chunk_bytes = max(256, cache_chunk_bytes)
        self._stream_emit_chunk_bytes = max(512, stream_emit_chunk_bytes)
        self._max_input_chars = max(32, max_input_chars)
        self._min_chunk_chars = max(16, min_chunk_chars)
        self._pcm_cache: OrderedDict[str, tuple[int, bytes]] = OrderedDict()
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    def _normalize_base_url(self, base_url: str) -> str:
        """Normalize user-provided base URL and make wildcard host routable for clients."""
        parsed = urlparse(base_url.strip())
        if not parsed.scheme or not parsed.netloc:
            return base_url.rstrip("/")

        hostname = parsed.hostname or ""
        if hostname != "0.0.0.0":
            return base_url.rstrip("/")

        # 0.0.0.0 is a bind address, not a routable destination.
        host = "127.0.0.1"
        if parsed.port is not None:
            netloc = f"{host}:{parsed.port}"
        else:
            netloc = host

        normalized = parsed._replace(netloc=netloc)
        return urlunparse(normalized).rstrip("/")

    def _can_cache_text(self, text: str) -> bool:
        return self._cache_enabled and bool(text) and len(text) <= self._cache_max_text_len

    def _get_cached_pcm(self, text: str) -> tuple[int, bytes] | None:
        item = self._pcm_cache.get(text)
        if item is None:
            return None
        self._pcm_cache.move_to_end(text)
        return item

    def _store_cached_pcm(self, text: str, sample_rate: int, pcm_bytes: bytes) -> None:
        if not self._can_cache_text(text) or not pcm_bytes:
            return
        self._pcm_cache[text] = (sample_rate, pcm_bytes)
        self._pcm_cache.move_to_end(text)
        while len(self._pcm_cache) > self._cache_max_items:
            self._pcm_cache.popitem(last=False)

    async def close(self) -> None:
        await self._client.aclose()

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _looks_like_code_or_noise(self, text: str) -> bool:
        if not text:
            return True

        lowered = text.lower()
        code_markers = (
            " def ",
            " class ",
            " import ",
            " return ",
            " if ",
            " else:",
            " for ",
            " while ",
            " => ",
            "();",
            "{}",
            "[]",
            "()",
        )
        marker_hits = sum(1 for marker in code_markers if marker in f" {lowered} ")

        total = len(text)
        alpha = sum(ch.isalpha() for ch in text)
        digits = sum(ch.isdigit() for ch in text)
        symbols = sum(not ch.isalnum() and not ch.isspace() for ch in text)

        alpha_ratio = alpha / total if total else 0.0
        symbol_ratio = symbols / total if total else 1.0
        digit_ratio = digits / total if total else 0.0

        # Too many symbols/digits and too little natural language.
        if alpha_ratio < 0.35 and (symbol_ratio > 0.28 or digit_ratio > 0.30):
            return True

        return marker_hits >= 2

    def prepare_text_for_tts(self, text: str) -> str:
        """Clean text and drop technical content that should not be spoken aloud."""
        if not text:
            return ""

        cleaned = text
        cleaned = _CODE_BLOCK_RE.sub(" ", cleaned)
        cleaned = _INLINE_CODE_RE.sub(" ", cleaned)
        cleaned = _URL_RE.sub(" ", cleaned)
        cleaned = _MD_LINK_RE.sub(r"\1", cleaned)
        cleaned = _TAG_RE.sub(" ", cleaned)
        cleaned = cleaned.replace("#", " ")

        kept_lines: list[str] = []
        for raw_line in cleaned.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Skip markdown table separators and bullet-only lines.
            if re.fullmatch(r"[-|: ]+", line):
                continue
            if re.fullmatch(r"[*\-_=~`><+\\/|]+", line):
                continue

            # Trim markdown bullets/quotes for better speech.
            line = re.sub(r"^[\-*>\d\.\)\s]+", "", line).strip()
            if not line:
                continue

            if self._looks_like_code_or_noise(line):
                continue

            kept_lines.append(line)

        if not kept_lines:
            return ""

        spoken = " ".join(kept_lines)
        spoken = _MULTI_PUNCT_RE.sub(r"\1", spoken)
        spoken = re.sub(r"\s+", " ", spoken).strip()

        # Final gate: avoid reading mostly symbols.
        if self._looks_like_code_or_noise(spoken):
            return ""

        return spoken

    async def _yield_pcm_buffered(
        self,
        sample_rate: int,
        chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[tuple[int, bytes]]:
        pending = bytearray()
        async for chunk in chunks:
            if not chunk:
                continue
            pending.extend(chunk)
            while len(pending) >= self._stream_emit_chunk_bytes:
                emit_size = self._stream_emit_chunk_bytes - (self._stream_emit_chunk_bytes % 2)
                if emit_size <= 0:
                    emit_size = len(pending) - (len(pending) % 2)
                if emit_size <= 0:
                    break
                yield sample_rate, bytes(pending[:emit_size])
                del pending[:emit_size]

        if pending:
            final_size = len(pending) - (len(pending) % 2)
            if final_size > 0:
                yield sample_rate, bytes(pending[:final_size])

    def _split_for_tts(self, text: str) -> list[str]:
        cleaned = self._normalize_text(text)
        if not cleaned:
            return []
        if len(cleaned) <= self._max_input_chars:
            return [cleaned]

        parts: list[str] = []
        cursor = 0
        length = len(cleaned)
        delimiters = ".!?;,:"

        while cursor < length:
            end = min(cursor + self._max_input_chars, length)
            if end >= length:
                chunk = cleaned[cursor:length].strip()
                if chunk:
                    parts.append(chunk)
                break

            split_at = -1
            for i in range(end, cursor + self._min_chunk_chars - 1, -1):
                if cleaned[i - 1] in delimiters:
                    split_at = i
                    break

            if split_at == -1:
                split_at = cleaned.rfind(" ", cursor + self._min_chunk_chars, end)

            if split_at == -1 or split_at <= cursor:
                split_at = end

            chunk = cleaned[cursor:split_at].strip()
            if chunk:
                parts.append(chunk)
            cursor = split_at

        return parts

    async def synthesize_wav(self, text: str) -> bytes | None:
        text = self.prepare_text_for_tts(text)
        if not text:
            return None

        payload = {
            "input": text,
            "voice": self._voice,
            "language": self._language,
            "instruct": self._instruct,
            "response_format": "wav",
            "do_sample": self._do_sample,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "top_k": self._top_k,
            "repetition_penalty": self._repetition_penalty,
            "max_new_tokens": self._max_new_tokens,
        }

        response = await self._client.post(f"{self._base_url}/v1/audio/speech", json=payload)
        if response.status_code >= 400:
            logger.error("TTS server error", extra={"status": response.status_code, "body": response.text})
            return None
        return response.content

    async def synthesize_pcm(self, text: str) -> bytes | None:
        text = self.prepare_text_for_tts(text)
        if not text:
            return None

        payload = {
            "input": text,
            "voice": self._voice,
            "language": self._language,
            "instruct": self._instruct,
            "response_format": "pcm",
            "do_sample": self._do_sample,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "top_k": self._top_k,
            "repetition_penalty": self._repetition_penalty,
            "max_new_tokens": self._max_new_tokens,
        }

        response = await self._client.post(f"{self._base_url}/v1/audio/speech", json=payload)
        if response.status_code >= 400:
            logger.error("TTS PCM fallback endpoint error", extra={"status": response.status_code, "body": response.text})
            return None
        return response.content

    async def _stream_single_text_pcm(self, text: str) -> AsyncIterator[tuple[int, bytes]]:
        text = self.prepare_text_for_tts(text)
        if not text:
            return

        if self._can_cache_text(text):
            cached = self._get_cached_pcm(text)
            if cached is not None:
                sample_rate, pcm_bytes = cached
                for idx in range(0, len(pcm_bytes), self._cache_chunk_bytes):
                    chunk = pcm_bytes[idx : idx + self._cache_chunk_bytes]
                    if chunk:
                        yield sample_rate, chunk
                return

        payload = {
            "input": text,
            "voice": self._voice,
            "language": self._language,
            "instruct": self._instruct,
            "response_format": "pcm",
            "do_sample": self._do_sample,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "top_k": self._top_k,
            "repetition_penalty": self._repetition_penalty,
            "max_new_tokens": self._max_new_tokens,
        }

        if self._use_streaming:
            try:
                cached_stream_pcm = bytearray()
                async with self._client.stream("POST", f"{self._base_url}/v1/audio/speech/stream", json=payload) as response:
                    if response.status_code >= 400:
                        logger.error(
                            "TTS stream endpoint error",
                            extra={"status": response.status_code, "body": (await response.aread()).decode("utf-8", errors="ignore")},
                        )
                    else:
                        sample_rate = int(response.headers.get("X-Sample-Rate", str(self._stream_sample_rate)))
                        async def _iter_stream_bytes() -> AsyncIterator[bytes]:
                            async for chunk in response.aiter_bytes():
                                if chunk:
                                    cached_stream_pcm.extend(chunk)
                                    yield chunk

                        async for buffered_sample_rate, buffered_chunk in self._yield_pcm_buffered(sample_rate, _iter_stream_bytes()):
                            yield buffered_sample_rate, buffered_chunk
                        self._store_cached_pcm(text, sample_rate, bytes(cached_stream_pcm))
                        return
            except Exception:
                logger.exception("TTS streaming endpoint failed; fallback to /v1/audio/speech")

        pcm_bytes = await self.synthesize_pcm(text)
        if pcm_bytes is None:
            return

        self._store_cached_pcm(text, self._stream_sample_rate, pcm_bytes)

        # Fallback compatibility: return whole PCM as a single chunk.
        yield self._stream_sample_rate, pcm_bytes

    async def stream_pcm(self, text: str) -> AsyncIterator[tuple[int, bytes]]:
        cleaned = self.prepare_text_for_tts(text)
        for part in self._split_for_tts(cleaned):
            async for sample_rate, chunk in self._stream_single_text_pcm(part):
                yield sample_rate, chunk
