from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env",), env_file_encoding="utf-8", extra="ignore")

    log_level: str = Field(default="INFO", description="Log level")

    azure_openai_api_key: SecretStr = Field(description="Azure OpenAI API key")
    azure_openai_api_version: str = Field(default="2024-02-01", description="API version")
    azure_openai_endpoint: str = Field(description="Azure OpenAI endpoint base URL")
    azure_openai_deployment: str = Field(description="Azure OpenAI deployment name")
    azure_openai_model_name: str = Field(description="Azure OpenAI model name")

    vector_index_path: str = Field(default="/tmp/luxis/data/vector_index.faiss", description="Path to FAISS index file")
    meta_index_path: str = Field(default="/tmp/luxis/data/meta_index.db", description="Path to metadata index DB")

    def __str__(self) -> str:
        masked = {}
        for k, v in self.model_dump().items():
            if "key" in k.lower() or "secret" in k.lower():
                if isinstance(v, SecretStr):
                    val = v.get_secret_value()
                else:
                    val = str(v)
                masked[k] = val[:3] + "***" + val[-3:] if len(val) > 6 else "***"
            else:
                masked[k] = v
        return "\n".join(f"{k}: {v}" for k, v in masked.items())


settings = Settings()
