from pathlib import Path

from assistant.config import settings

# The one and only path this assistant is authorised to read/write.
# Resolved once at import time to prevent path-traversal at runtime.
_ALLOWED: Path = settings.practice_file_path.resolve()


def _guard() -> Path:
    """Return the resolved allowed path (security checkpoint)."""
    return _ALLOWED


def read_practice_file() -> str:
    path = _guard()
    if not path.exists():
        return "# practice.py — файл ещё пуст\n"
    return path.read_text(encoding="utf-8")


def write_practice_file(content: str) -> str:
    """Overwrite the entire practice file."""
    path = _guard()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"✅ practice.py перезаписан ({len(content)} символов)."


def append_to_practice_file(content: str) -> str:
    """Append *content* to the practice file, ensuring a blank-line separator."""
    path = _guard()
    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    # Ensure there is exactly one blank line between blocks
    separator = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    path.write_text(existing + separator + content, encoding="utf-8")
    return f"✅ Добавлено в practice.py ({len(content)} символов)."
