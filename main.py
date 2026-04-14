"""
main.py — real-time voice CLI for the ML Interview Assistant.

Run:
    python main.py

Behavior:
- Hold X to record from microphone (push-to-talk).
- When X is released, audio is transcribed and sent to the assistant.
- Assistant response is printed in terminal.
- Stop with Ctrl+C.
"""
from __future__ import annotations

import asyncio
import ctypes
import platform
import queue
import re
import threading
import time
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

from assistant.config import settings
from assistant.core.assistant import MLAssistant
from assistant.voice import stt

_assistant: MLAssistant | None = None
_THINK_BLOCK_RE = re.compile(r"<think>.*?(</think>|$)", flags=re.IGNORECASE | re.DOTALL)
_THINK_CLOSE_RE = re.compile(r"</think>", flags=re.IGNORECASE)


def _get_assistant() -> MLAssistant:
    global _assistant
    if _assistant is None:
        _assistant = MLAssistant()
    return _assistant


@dataclass(frozen=True)
class VoiceConfig:
    sample_rate: int = 16_000
    frame_ms: int = 20
    ptt_key: str = "x"
    min_ptt_ms: int = 150

    @property
    def frame_samples(self) -> int:
        return int(self.sample_rate * self.frame_ms / 1000)

    @property
    def min_ptt_frames(self) -> int:
        return max(1, self.min_ptt_ms // self.frame_ms)


class PushToTalkState:
    """Tracks whether the configured key is currently pressed."""

    def __init__(self, key_char: str = "x") -> None:
        self.key_char = key_char.lower()
        self._is_windows = platform.system().lower().startswith("win")

        # Windows: use low-level async key state polling (more reliable in terminals)
        self._vk: int | None = None
        if self._is_windows:
            self._vk = ord(self.key_char.upper())

        # Non-Windows fallback: pynput listener
        self._pressed = False
        self._lock = threading.Lock()
        self._listener = None
        if not self._is_windows:
            try:
                from pynput import keyboard  # lazy import

                self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            except Exception:  # noqa: BLE001
                self._listener = None

    def _matches(self, key) -> bool:
        try:
            ch = getattr(key, "char", None)
            return isinstance(ch, str) and ch.lower() == self.key_char
        except Exception:  # noqa: BLE001
            return False

    def _on_press(self, key) -> None:
        if self._matches(key):
            with self._lock:
                self._pressed = True

    def _on_release(self, key) -> None:
        if self._matches(key):
            with self._lock:
                self._pressed = False

    def start(self) -> None:
        if self._listener is not None:
            self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()

    def is_pressed(self) -> bool:
        if self._is_windows and self._vk is not None:
            state = ctypes.windll.user32.GetAsyncKeyState(self._vk)
            return bool(state & 0x8000)

        with self._lock:
            return self._pressed

    def backend_name(self) -> str:
        if self._is_windows:
            return "winapi(GetAsyncKeyState)"
        if self._listener is not None:
            return "pynput"
        return "unavailable"


class RealtimeVoiceCapture:
    """Microphone capture for push-to-talk segmentation."""

    def __init__(self, cfg: VoiceConfig) -> None:
        self.cfg = cfg

    def capture_ptt_utterance(self, ptt: PushToTalkState) -> np.ndarray | None:
        """Record while key is held. Returns normalized mono float32 audio."""
        audio_queue: queue.Queue[bytes] = queue.Queue()

        def callback(indata, frames, time_info, status) -> None:
            if status:
                return
            audio_queue.put(bytes(indata))

        speech_frames: list[bytes] = []

        with sd.RawInputStream(
            samplerate=self.cfg.sample_rate,
            blocksize=self.cfg.frame_samples,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            # Wait for key press, drop queued noise while idle.
            while not ptt.is_pressed():
                try:
                    audio_queue.get(timeout=0.05)
                except queue.Empty:
                    time.sleep(0.01)

            # Record strictly while key is held.
            while ptt.is_pressed():
                try:
                    frame = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                speech_frames.append(frame)

            # Keep tiny trailing tail to avoid abrupt cutoff.
            for _ in range(2):
                try:
                    speech_frames.append(audio_queue.get(timeout=0.02))
                except queue.Empty:
                    break

        if len(speech_frames) < self.cfg.min_ptt_frames:
            return None

        pcm = np.frombuffer(b"".join(speech_frames), dtype=np.int16).astype(np.float32)
        return pcm / 32768.0


def _strip_think_sections(text: str) -> str:
    """Remove hidden reasoning blocks from model output."""
    cleaned = _THINK_BLOCK_RE.sub("", text)
    return _THINK_CLOSE_RE.sub("", cleaned)


def _map_spoken_command(text: str) -> str:
    """Map spoken Russian phrases to slash commands for hands-free control."""
    normalized = " ".join(text.lower().strip().split())
    if not normalized:
        return text

    if normalized.startswith("/"):
        return text

    if any(k in normalized for k in ("режим интервью", "интервью режим", "mock interview")):
        return "/mode interview"

    if any(k in normalized for k in ("режим диагностики", "диагностический режим", "режим проверк", "квиз режим")):
        return "/mode diagnostic"

    if any(k in normalized for k in ("режим обучения", "режим study", "обычный режим", "режим ментор")):
        return "/mode study"

    if any(k in normalized for k in ("статус режима", "какой режим", "текущий режим")):
        return "/mode status"

    if normalized in ("помощь", "команды", "список команд", "help"):
        return "/help"

    return text


async def stream_answer(assistant: MLAssistant, user_text: str) -> str:
    """Stream LLM tokens to terminal (text-only, no TTS)."""
    raw_text = ""
    visible_text = ""
    print("Ассистент: ", end="", flush=True)

    async for delta in assistant.stream_chat(user_text):
        if not delta:
            continue

        raw_text += delta
        cleaned = _strip_think_sections(raw_text)

        # Incremental diff to avoid re-printing full content every token.
        if cleaned.startswith(visible_text):
            delta_visible = cleaned[len(visible_text):]
        else:
            delta_visible = cleaned
            visible_text = ""

        if not delta_visible:
            continue

        print(delta_visible, end="", flush=True)
        visible_text += delta_visible

    print("\n")
    return visible_text.strip()


async def run_cli() -> None:
    assistant = _get_assistant()
    cfg = VoiceConfig()
    capture = RealtimeVoiceCapture(cfg)
    ptt = PushToTalkState(cfg.ptt_key)
    loop = asyncio.get_running_loop()
    ptt.start()
    interactions_since_save = 0
    last_auto_save_ts = time.monotonic()

    print("ML Voice Assistant запущен.")
    print(f"Удерживай '{cfg.ptt_key.upper()}' для записи. Остановка: Ctrl+C")
    print(f"PTT backend: {ptt.backend_name()}")
    print("Команды: /mode study | /mode diagnostic | /mode interview | /mode status | /help")
    print("Голосом: 'режим интервью', 'режим диагностики', 'режим обучения', 'статус режима', 'помощь'")
    print(
        "Автосохранение: "
        f"каждые {settings.auto_save_every_turns} диалога(ов), "
        f"не чаще чем раз в {settings.auto_save_min_interval_sec} сек."
    )

    try:
        while True:
            audio = await loop.run_in_executor(None, capture.capture_ptt_utterance, ptt)
            if audio is None:
                continue

            user_text = await loop.run_in_executor(None, stt.transcribe, audio, cfg.sample_rate)
            if not user_text.strip():
                continue

            mapped = _map_spoken_command(user_text)
            if mapped.startswith("/") and mapped != user_text:
                print(f"\nТы (voice-command): {mapped}")
                user_text = mapped

            print(f"\nТы: {user_text}")

            user_text = user_text
            _ = await stream_answer(assistant, user_text)
            interactions_since_save += 1

            if (
                interactions_since_save >= settings.auto_save_every_turns
                and (time.monotonic() - last_auto_save_ts) >= settings.auto_save_min_interval_sec
            ):
                status = await assistant.save_session()
                if not status.startswith("Недостаточно диалога"):
                    print(f"[autosave] {status}")
                interactions_since_save = 0
                last_auto_save_ts = time.monotonic()

    except KeyboardInterrupt:
        print("\nЗавершение сессии и сохранение памяти...")
        status = await assistant.save_session()
        print(status)
    finally:
        ptt.stop()


if __name__ == "__main__":
    asyncio.run(run_cli())
