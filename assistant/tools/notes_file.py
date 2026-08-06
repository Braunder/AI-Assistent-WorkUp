from datetime import datetime
from pathlib import Path

from assistant.config import settings

_ALLOWED: Path = settings.notes_file_path.resolve()


def _guard() -> Path:
    return _ALLOWED


def read_notes_file() -> str:
    path = _guard()
    if not path.exists():
        return "Пока нет записей."
    return path.read_text(encoding="utf-8")


def append_note(content: str, title: str = "") -> str:
    path = _guard()
    path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"[{now}]"
    if title.strip():
        header += f" {title.strip()}"

    block = f"{header}\n{content.strip()}\n\n"

    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(existing + block, encoding="utf-8")
    return "✅ Запись добавлена в study_notes.txt"
