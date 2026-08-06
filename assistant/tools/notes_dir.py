from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from assistant.config import settings

_NOTES_DIR: Path = settings.notes_dir_path.resolve()
_NOTES_DIR.mkdir(parents=True, exist_ok=True)

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_\-\. ]+")


def _slugify(name: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("_", name.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = cleaned.strip("._")
    return cleaned or "note"


def _guard_path(file_name: str) -> Path:
    safe = _slugify(file_name)
    if not safe.lower().endswith(".md"):
        safe += ".md"
    path = (_NOTES_DIR / safe).resolve()
    if _NOTES_DIR not in path.parents and path != _NOTES_DIR:
        raise ValueError("Недопустимый путь файла заметки")
    return path


def list_note_files() -> str:
    files = sorted(p.name for p in _NOTES_DIR.glob("*.md"))
    if not files:
        return "Папка notes пока пуста."
    return "\n".join(f"- {name}" for name in files)


def write_note_file(title: str, content: str) -> str:
    path = _guard_path(title)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = content.strip()
    if not body:
        return "❌ Пустая заметка: content обязателен"

    header = f"# {title.strip() or path.stem}\n\n_Обновлено: {now}_\n\n"
    path.write_text(header + body + "\n", encoding="utf-8", newline="\n")
    return f"✅ Заметка сохранена: notes/{path.name}"


def read_note_file(file_name: str) -> str:
    path = _guard_path(file_name)
    if not path.exists():
        return f"❌ Файл не найден: notes/{path.name}"
    return path.read_text(encoding="utf-8")


def append_note_file(file_name: str, content: str) -> str:
    path = _guard_path(file_name)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = content.strip()
    if not text:
        return "❌ Пустой append: content обязателен"

    if path.exists():
        existing = path.read_text(encoding="utf-8").rstrip() + "\n\n"
    else:
        existing = f"# {path.stem}\n\n"

    block = f"## {now}\n{text}\n"
    path.write_text(existing + block, encoding="utf-8", newline="\n")
    return f"✅ Дополнено: notes/{path.name}"
