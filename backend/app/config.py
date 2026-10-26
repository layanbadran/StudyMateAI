"""All settings live here. They are read from environment variables (.env file)."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Properties read the environment each time, so changes (and tests) take effect immediately.
    @property
    def anthropic_api_key(self) -> str:
        return os.getenv("ANTHROPIC_API_KEY", "").strip()

    @property
    def llm_provider(self) -> str:
        return os.getenv("LLM_PROVIDER", "anthropic").strip().lower()

    @property
    def ollama_model(self) -> str:
        return os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    @property
    def ollama_url(self) -> str:
        return os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

    @property
    def llm_ready(self) -> bool:
        """Ollama needs no key. Anthropic needs ANTHROPIC_API_KEY."""
        return self.llm_provider == "ollama" or bool(self.anthropic_api_key)

    @property
    def anthropic_model(self) -> str:
        return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    @property
    def embedding_model(self) -> str:
        return os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )

    @property
    def chroma_dir(self) -> str:
        return os.getenv("CHROMA_DIR", "./chroma_data")

    @property
    def max_upload_mb(self) -> int:
        return int(os.getenv("MAX_UPLOAD_MB", "20"))

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def chunk_size(self) -> int:
        return int(os.getenv("CHUNK_SIZE", "1000"))

    @property
    def chunk_overlap(self) -> int:
        return int(os.getenv("CHUNK_OVERLAP", "200"))

    @property
    def top_k(self) -> int:
        return int(os.getenv("TOP_K", "5"))

    @property
    def max_distance(self) -> float:
        return float(os.getenv("MAX_DISTANCE", "0.85"))

    @property
    def frontend_origin(self) -> str:
        return os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


settings = Settings()