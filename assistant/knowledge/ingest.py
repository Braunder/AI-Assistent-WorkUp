from __future__ import annotations

import hashlib
from pathlib import Path

from assistant.config import settings
from assistant.memory.store import MemoryStore


def _read_corpus(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _chunk_section(text: str, target_chars: int = 1400) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= target_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)

    return chunks


def build_chunks(corpus_text: str) -> list[dict[str, str]]:
    sections = corpus_text.split("## ")
    chunks: list[dict[str, str]] = []

    for raw_section in sections:
        section = raw_section.strip()
        if not section:
            continue

        lines = section.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if not body:
            continue

        sources = [
            line.split("Source:", 1)[1].strip()
            for line in body.splitlines()
            if line.startswith("Source:")
        ]
        source = " | ".join(sources) if sources else "unknown"

        for idx, piece in enumerate(_chunk_section(body), start=1):
            raw_id = f"{title}|{idx}|{piece}"
            digest = hashlib.sha1(raw_id.encode("utf-8")).hexdigest()
            chunks.append(
                {
                    "id": f"kb_{digest}",
                    "title": title,
                    "source": source,
                    "text": piece,
                }
            )

    return chunks


def ingest_knowledge_corpus() -> tuple[int, int]:
    corpus_path = settings.knowledge_corpus_path
    if not corpus_path.exists():
        raise FileNotFoundError(f"Knowledge corpus not found: {corpus_path}")

    corpus_text = _read_corpus(corpus_path)
    chunks = build_chunks(corpus_text)

    store = MemoryStore()
    inserted = store.upsert_knowledge_chunks(chunks)
    total = store.knowledge_count()
    return inserted, total


if __name__ == "__main__":
    inserted_count, total_count = ingest_knowledge_corpus()
    print(f"Inserted/updated chunks: {inserted_count}")
    print(f"Total knowledge chunks in collection: {total_count}")
