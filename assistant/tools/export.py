"""Export assistant session data to Markdown and PDF."""
from __future__ import annotations

from datetime import datetime
import json


def export_to_markdown(
    notes: str,
    progress: list[str],
    weak_topics: list[str],
    chat_messages: list[dict[str, str]] | None = None,
    max_chat_messages: int = 120,
) -> str:
    """Build a Markdown document from session data for download."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        "# ML Interview Assistant — Export",
        f"_Дата экспорта: {now}_\n",
    ]

    if progress:
        lines.append("## ✅ Прогресс по темам\n")
        for item in progress:
            lines.append(f"- {item}")
        lines.append("")

    if weak_topics:
        lines.append("## ⚠️ Слабые места\n")
        for item in weak_topics:
            lines.append(f"- {item}")
        lines.append("")

    if notes.strip():
        lines.append("## 📝 Заметки из сессий\n")
        lines.append(notes)

    # Include current Streamlit chat transcript so exports are useful even
    # when progress/notes are still empty.
    if chat_messages:
        lines.append("")
        lines.append("## 💬 Диалог (текущая сессия)\n")
        tail = chat_messages[-max_chat_messages:]
        for msg in tail:
            role = (msg.get("role") or "unknown").strip().lower()
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            role_label = "Пользователь" if role == "user" else "Ассистент"
            lines.append(f"### {role_label}")
            lines.append(content)
            lines.append("")

    return "\n".join(lines)


def import_chat_from_json(raw_text: str) -> list[dict[str, str]]:
    """Load chat messages from JSON payload: [{"role": ..., "content": ...}, ...]."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Некорректный JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("JSON должен быть списком сообщений.")

    messages: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            continue
        role_norm = role.strip().lower()
        if role_norm not in ("user", "assistant"):
            continue
        text = content.strip()
        if not text:
            continue
        messages.append({"role": role_norm, "content": text})

    return messages


def import_chat_from_markdown(raw_text: str) -> list[dict[str, str]]:
    """
    Parse exported Markdown chat sections.

    Expected blocks:
    ### Пользователь
    ...
    ### Ассистент
    ...
    """
    lines = raw_text.splitlines()
    messages: list[dict[str, str]] = []
    current_role: str | None = None
    buffer: list[str] = []

    def _flush() -> None:
        nonlocal current_role, buffer
        if current_role and buffer:
            text = "\n".join(buffer).strip()
            if text:
                messages.append({"role": current_role, "content": text})
        buffer = []

    for line in lines:
        if line.startswith("### "):
            _flush()
            label = line[4:].strip().lower()
            if "пользователь" in label or label == "user":
                current_role = "user"
            elif "ассистент" in label or label == "assistant":
                current_role = "assistant"
            else:
                current_role = None
            continue

        if current_role is not None:
            buffer.append(line)

    _flush()
    return messages


def export_to_pdf(markdown_content: str) -> bytes:
    """
    Convert Markdown text to a PDF bytes object for st.download_button.

    Requires: pip install fpdf2
    Uses Windows Arial (Cyrillic + Unicode) when available; otherwise
    sanitises the text to Latin-1 before falling back to Helvetica.
    """
    try:
        from fpdf import FPDF  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "fpdf2 is required for PDF export. Install it: pip install fpdf2"
        ) from exc

    import pathlib

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Font selection: prefer a Unicode TTF (Arial on Windows) ---
    font_name = "Helvetica"
    unicode_ok = False

    _unicode_candidates: list[tuple[str, str, pathlib.Path]] = [
        ("Arial", "",  pathlib.Path("C:/Windows/Fonts/arial.ttf")),
        ("Arial", "B", pathlib.Path("C:/Windows/Fonts/arialbd.ttf")),
        ("Verdana", "",  pathlib.Path("C:/Windows/Fonts/verdana.ttf")),
        ("Verdana", "B", pathlib.Path("C:/Windows/Fonts/verdanab.ttf")),
    ]

    registered_family: str | None = None
    try:
        for family, style, path in _unicode_candidates:
            if path.exists():
                pdf.add_font(family, style, str(path))
                if registered_family is None:
                    registered_family = family
        if registered_family:
            font_name = registered_family
            unicode_ok = True
    except Exception:
        font_name = "Helvetica"
        unicode_ok = False

    def _safe(text: str) -> str:
        """
        Strip characters the font cannot render.

        Always removes emoji/symbol-range codepoints (plane 1+, or Unicode
        symbol categories) because even Arial/Verdana TTF fonts rarely
        include them.  For the Helvetica fallback, also converts common
        Unicode punctuation to ASCII and drops remaining non-Latin-1 chars.
        """
        import unicodedata

        cleaned: list[str] = []
        for ch in text:
            cp = ord(ch)
            # Drop supplementary-plane characters (emoji, flags, etc.)
            if cp > 0xFFFF:
                continue
            # Drop variation selectors (U+FE00–U+FE1F) — invisible modifiers
            if 0xFE00 <= cp <= 0xFE1F:
                continue
            # Drop combining marks (e.g. U+20E3 keycap overlay) that common
            # Windows fonts frequently miss and that are not essential here.
            if unicodedata.category(ch) in ("Mn", "Mc", "Me") and cp > 127:
                continue
            # Drop Unicode symbol/misc-symbol categories (emoji in BMP)
            if unicodedata.category(ch) in ("So", "Sm") and cp > 127:
                continue
            cleaned.append(ch)
        result = "".join(cleaned)

        if unicode_ok:
            return result

        # Latin-1 sanitisation for Helvetica fallback
        return (
            result
            .replace("\u2014", "-")
            .replace("\u2013", "-")
            .replace("\u2019", "'")
            .replace("\u2018", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2026", "...")
            .encode("latin-1", errors="replace")
            .decode("latin-1")
        )

    pdf.set_font(font_name, size=11)

    # epw = effective page width (respects left/right margins)
    for line in markdown_content.splitlines():
        if line.startswith("# "):
            pdf.set_font(font_name, style="B", size=16)
            pdf.multi_cell(pdf.epw, 10, _safe(line[2:]))
            pdf.set_font(font_name, size=11)
        elif line.startswith("## "):
            pdf.set_font(font_name, style="B", size=13)
            pdf.multi_cell(pdf.epw, 8, _safe(line[3:]))
            pdf.set_font(font_name, size=11)
        elif line.startswith("- "):
            pdf.multi_cell(pdf.epw, 7, _safe(f"  - {line[2:]}"))
        elif line.strip():
            pdf.multi_cell(pdf.epw, 7, _safe(line))
        else:
            pdf.ln(3)

    # Streamlit download_button rejects bytearray; normalise to bytes.
    return bytes(pdf.output())
