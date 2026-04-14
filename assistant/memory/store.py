from __future__ import annotations

import hashlib

import chromadb
from openai import OpenAI

from assistant.config import settings
from assistant.memory.schema import MemoryEntry, MemoryType


class LMStudioEmbeddingFunction:
    """Chroma-compatible embedding function backed by LM Studio."""

    def __init__(self, base_url: str, model: str) -> None:
        self._client = OpenAI(base_url=base_url, api_key="lm-studio")
        self._model = model

    def _prepare_inputs(self, input: list[str]) -> list[str]:
        """Apply optional token suffix workaround for specific GGUF embedding models."""
        if not settings.embedding_append_eos:
            return input
        suffix = settings.embedding_eos_token
        prepared: list[str] = []
        for text in input:
            clean = (text or "").rstrip()
            prepared.append(f"{clean} {suffix}" if clean else suffix)
        return prepared

    def _embed(self, input: list[str]) -> list[list[float]]:
        if not input:
            return []

        prepared_input = self._prepare_inputs(input)
        response = self._client.embeddings.create(model=self._model, input=prepared_input)
        # Preserve order by index as returned by provider.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._embed(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self._embed(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self._embed(input)

    def name(self) -> str:
        return f"lmstudio:{self._model}"


class MemoryStore:
    """Persistent ChromaDB vector store for cross-session RAG memory."""

    def __init__(self) -> None:
        settings.memory_db_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(settings.memory_db_path))
        ef = LMStudioEmbeddingFunction(
            base_url=settings.lm_studio_base_url,
            model=settings.lm_studio_embedding_model,
        )

        self._collection = self._client.get_or_create_collection(
            name="assistant_memory",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._knowledge_collection = self._client.get_or_create_collection(
            name="assistant_knowledge",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, entry: MemoryEntry) -> None:
        self._collection.add(
            ids=[entry.id],
            documents=[entry.content],
            metadatas=[
                {
                    "type": entry.type.value,
                    "timestamp": entry.timestamp.isoformat(),
                    **entry.metadata,
                }
            ],
        )

    def query(self, text: str, n_results: int | None = None) -> list[str]:
        """Return the most semantically relevant stored memories."""
        count = self._collection.count()
        if count == 0:
            return []

        k = min(n_results or settings.max_context_memories, count)
        results = self._collection.query(query_texts=[text], n_results=k)

        docs: list[str] = results.get("documents", [[]])[0]
        return docs

    def get_by_type(self, *types: MemoryType) -> list[str]:
        """Fetch all entries of given types (for progress overview)."""
        if self._collection.count() == 0:
            return []

        results = self._collection.get(
            where={"type": {"$in": [t.value for t in types]}}
        )
        return results.get("documents") or []

    def count(self) -> int:
        return self._collection.count()

    def upsert_knowledge_chunks(self, chunks: list[dict[str, str]]) -> int:
        """Upsert curated knowledge chunks into a dedicated collection."""
        if not chunks:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, str]] = []

        for chunk in chunks:
            text = (chunk.get("text") or "").strip()
            if not text:
                continue

            source = (chunk.get("source") or "unknown").strip()
            title = (chunk.get("title") or "knowledge").strip()
            chunk_id = chunk.get("id")
            if not chunk_id:
                digest = hashlib.sha1(f"{source}|{title}|{text}".encode("utf-8")).hexdigest()
                chunk_id = f"k_{digest}"

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append({"type": "knowledge", "source": source, "title": title})

        if not ids:
            return 0

        self._knowledge_collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)

    def query_knowledge(self, text: str, n_results: int | None = None) -> list[str]:
        """Return relevant knowledge chunks with source markers for grounding."""
        count = self._knowledge_collection.count()
        if count == 0:
            return []

        k = min(n_results or settings.max_knowledge_context_chunks, count)
        results = self._knowledge_collection.query(
            query_texts=[text],
            n_results=k,
            include=["documents", "metadatas"],
        )

        docs: list[str] = results.get("documents", [[]])[0]
        metas: list[dict[str, str]] = results.get("metadatas", [[]])[0]
        formatted: list[str] = []
        for doc, meta in zip(docs, metas):
            source = (meta or {}).get("source", "unknown")
            title = (meta or {}).get("title", "knowledge")
            formatted.append(f"[{title} | {source}] {doc}")
        return formatted

    def query_with_metadata(self, text: str, n_results: int | None = None) -> list[dict]:
        """Return session memories with metadata for RAG transparency in UI."""
        count = self._collection.count()
        if count == 0:
            return []

        k = min(n_results or settings.max_context_memories, count)
        results = self._collection.query(
            query_texts=[text],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        docs: list[str] = results.get("documents", [[]])[0]
        metas: list[dict] = results.get("metadatas", [[]])[0]
        dists: list[float] = results.get("distances", [[]])[0]
        return [
            {
                "text": doc,
                "source": (meta or {}).get("timestamp", "session memory"),
                "type": (meta or {}).get("type", "session"),
                "score": round(max(0.0, 1.0 - dist), 3),
            }
            for doc, meta, dist in zip(docs, metas, dists)
        ]

    def query_knowledge_with_metadata(self, text: str, n_results: int | None = None) -> list[dict]:
        """Return knowledge chunks with metadata for RAG transparency in UI."""
        count = self._knowledge_collection.count()
        if count == 0:
            return []

        k = min(n_results or settings.max_knowledge_context_chunks, count)
        results = self._knowledge_collection.query(
            query_texts=[text],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        docs: list[str] = results.get("documents", [[]])[0]
        metas: list[dict] = results.get("metadatas", [[]])[0]
        dists: list[float] = results.get("distances", [[]])[0]
        return [
            {
                "text": doc[:250] + "..." if len(doc) > 250 else doc,
                "source": (meta or {}).get("source", "knowledge base"),
                "type": "knowledge",
                "score": round(max(0.0, 1.0 - dist), 3),
            }
            for doc, meta, dist in zip(docs, metas, dists)
        ]

    def knowledge_count(self) -> int:
        return self._knowledge_collection.count()
