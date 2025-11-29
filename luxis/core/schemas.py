from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, SecretStr, model_validator


class AIProviders(str, Enum):
    OpenAI = "OpenAI"
    AzureOpenAI = "AzureOpenAI"


class AzureOpenAISettings(BaseModel):
    azure_openai_api_key: SecretStr = Field(..., description="Azure OpenAI API key")
    azure_openai_api_version: str = Field(..., description="Azure OpenAI API version")
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI endpoint base URL")
    azure_openai_deployment: str = Field(..., description="Azure OpenAI deployment name")
    azure_openai_model_name: str = Field(..., description="Azure OpenAI model name")


class OpenAISettings(BaseModel):
    openai_api_key: SecretStr = Field(..., description="OpenAI API key")
    openai_model_name: str = Field(..., description="OpenAI model name")


class IngestConfig(BaseModel):
    embedding_dim: int = Field(default=1536, description="Embedding vector dimension")


class QueryConfig(BaseModel):
    top_k: int = Field(default=10, description="Number of nearest neighbors to return")


class Directories(BaseModel):
    path: Path = Field(default=Path("./luxis"), description="Base directory path")
    include: List[str] = Field(default=["**"], description="Patterns to include")
    ignore: List[str] = Field(
        default=[
            ".venv/**",
            ".git/**",
            ".idea/**",
            "**/__pycache__/**",
            "**/.cache/**",
            "**/cache/**",
            "**/*cache*/**",
        ],
        description="Ignored patterns",
    )


class GeneralSettings(BaseModel):
    log_level: str = Field(default="INFO", description="Log level")
    vector_index_path: str = Field(
        default="/tmp/luxis/data/vector_index.faiss",
        description="Path to FAISS index file",
    )
    meta_index_path: str = Field(
        default="/tmp/luxis/data/meta_index.db",
        description="Path to metadata index DB",
    )
    ai_provider: AIProviders = Field(default=AIProviders.OpenAI, description="AI provider selection")


class Config(BaseModel):
    settings: GeneralSettings = Field(default=GeneralSettings(), description="General settings")
    azure_settings: Optional[AzureOpenAISettings] = Field(default=None, description="Azure OpenAI settings")
    openai_settings: Optional[OpenAISettings] = Field(default=None, description="OpenAI settings")
    ingest: IngestConfig = Field(default_factory=IngestConfig, description="Ingestion configuration")
    query: QueryConfig = Field(default_factory=QueryConfig, description="Query configuration")
    directories: List[Directories] = Field(default_factory=lambda: [Directories()])

    @model_validator(mode="after")
    def validate_provider_settings(self):
        if self.settings.ai_provider == AIProviders.AzureOpenAI and not self.azure_settings:
            raise ValueError("AzureOpenAI selected but azure_settings section missing or incomplete.")
        if self.settings.ai_provider == AIProviders.OpenAI and not self.openai_settings:
            raise ValueError("OpenAI selected but openai_settings section missing or incomplete.")
        return self
