"""Configuration settings for Ragent."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_DB_")

    host: str = "localhost"
    port: int = 5432
    user: str = "ragent"
    password: str = "ragent"
    name: str = "ragent"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class VectorDBSettings(BaseSettings):
    """Vector database configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_VECTOR_")

    # PgVector
    pgvector_enabled: bool = True

    # Milvus
    milvus_enabled: bool = False
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_user: str = ""
    milvus_password: str = ""
    milvus_secure: bool = False

    @property
    def milvus_uri(self) -> str:
        if self.milvus_user and self.milvus_password:
            return f"http://{self.milvus_user}:{self.milvus_password}@{self.milvus_host}:{self.milvus_port}"
        return f"http://{self.milvus_host}:{self.milvus_port}"


class ObjectStorageSettings(BaseSettings):
    """Object storage (MinIO/S3) configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_STORAGE_")

    endpoint: str = "localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "ragent"
    secure: bool = False
    region: str = "us-east-1"


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_LLM_")

    provider: str = "mock"  # mock, openai, qwen, glm, llama
    model: str = "mock-gpt-4"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    timeout: float = 30.0
    max_retries: int = 3


class EmbeddingSettings(BaseSettings):
    """Embedding provider configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_EMBEDDING_")

    provider: str = "mock"  # mock, openai, qwen, jina, bge
    model: str = "mock-embedding"
    api_key: str | None = None
    base_url: str | None = None
    dimension: int = 768
    timeout: float = 30.0
    max_retries: int = 3


class RetrievalSettings(BaseSettings):
    """Retrieval configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_RETRIEVAL_")

    top_k: int = 10
    bm25_weight: float = 0.3
    vector_weight: float = 0.7
    rerank_enabled: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_k: int = 5


class IngestSettings(BaseSettings):
    """Document ingestion configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_INGEST_")

    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 100
    supported_extensions: list[str] = Field(default_factory=lambda: [
        ".pdf", ".docx", ".txt", ".md", ".html", ".htm",
        ".png", ".jpg", ".jpeg", ".gif", ".webp",
        ".mp4", ".mov", ".avi", ".mkv",
        ".mp3", ".wav", ".flac", ".m4a",
    ])


class APISettings(BaseSettings):
    """API server configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_API_")

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    rate_limit: int = 100  # requests per minute


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="RAGENT_LOG_")

    level: str = "INFO"
    format: str = "json"  # json, console
    file: str | None = None


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    vector_db: VectorDBSettings = Field(default_factory=VectorDBSettings)
    storage: ObjectStorageSettings = Field(default_factory=ObjectStorageSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    ingest: IngestSettings = Field(default_factory=IngestSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    environment: str = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def configure_logging(settings: Settings) -> None:
    """Configure structlog based on settings."""
    import structlog

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.logging.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), settings.logging.level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )