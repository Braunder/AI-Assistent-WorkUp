from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to the workspace root (parent of this package dir)
_WORKSPACE_ROOT = Path(__file__).parent.parent
_ENV_FILE = _WORKSPACE_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- LLM ---
    lm_studio_base_url: str = "http://localhost:8080/v1"
    lm_studio_model: str = "qwen3.5-9b"
    lm_studio_embedding_model: str = "text-embedding-qwen3-embedding-0.6b"
    lm_studio_embedding_base_url: str = "http://localhost:1234/v1"

    # --- Tavily ---
    tavily_api_key: str = ""

    # --- File access (only this path is writable by the assistant) ---
    practice_file_path: Path = _WORKSPACE_ROOT / "practice.py"
    notes_file_path: Path = _WORKSPACE_ROOT / "study_notes.txt"
    notes_dir_path: Path = _WORKSPACE_ROOT / "notes"

    # --- RAG memory ---
    memory_db_path: Path = _WORKSPACE_ROOT / "memory_db"
    knowledge_corpus_path: Path = _WORKSPACE_ROOT / "KNOWLEDGE_RAG_MLOPS_LMOPS.md"
    max_context_memories: int = 5
    max_knowledge_context_chunks: int = 6
    # Optional workaround for GGUF embedding models that warn about missing SEP/EOS.
    # Keep disabled by default to preserve baseline embedding behavior.
    embedding_append_eos: bool = False
    embedding_eos_token: str = "<|endoftext|>"
    auto_save_every_turns: int = 2
    auto_save_min_interval_sec: int = 120

    # --- Voice ---
    whisper_model: str = "medium"
    tts_enabled: bool = True
    tts_base_url: str = "http://0.0.0.0:8001"
    tts_timeout_seconds: float = 45.0
    tts_voice: str = "utena"
    tts_language: str = "russian"
    tts_instruct: str = "Говори спокойно и разборчиво на русском языке."
    tts_do_sample: bool = True
    tts_temperature: float = 0.4
    tts_top_p: float = 0.9
    tts_top_k: int = 40
    tts_repetition_penalty: float = 1.05
    tts_max_new_tokens: int = 1200
    tts_use_streaming: bool = True
    tts_stream_sample_rate: int = 24000
    tts_cache_enabled: bool = True
    tts_cache_max_items: int = 64
    tts_cache_max_text_len: int = 1200
    tts_cache_chunk_bytes: int = 4096
    tts_stream_emit_chunk_bytes: int = 8192
    tts_max_input_chars: int = 450
    tts_min_chunk_chars: int = 60

    # --- Streamlit UI ---
    streamlit_port: int = 8501
    interview_timer_minutes: int = 20

    @property
    def workspace_root(self) -> Path:
        return _WORKSPACE_ROOT


settings = Settings()
