import json
import tiktoken

from pathlib import Path
from typing import Any, Dict, List, Tuple
from openai import AsyncOpenAI, AsyncAzureOpenAI
from tika import parser

from luxis.utils.logger import logger
from luxis.core.schemas import AIProviders


async def _build_client(config):
    if config.settings.ai_provider == AIProviders.AzureOpenAI:
        s = config.azure_settings
        logger.debug(s.azure_openai_api_key.get_secret_value())
        logger.debug(s)
        return AsyncAzureOpenAI(
            api_key=s.azure_openai_api_key.get_secret_value(),
            api_version=s.azure_openai_api_version,
            azure_endpoint=s.azure_openai_endpoint,
            azure_deployment=s.azure_openai_deployment,
        )
    elif config.settings.ai_provider == AIProviders.OpenAI:
        s = config.openai_settings
        logger.debug(s.openai_api_key.get_secret_value())
        logger.debug(s)
        return AsyncOpenAI(api_key=s.openai_api_key.get_secret_value())
    else:
        raise ValueError(f"Unsupported ai_provider: {config.settings.ai_provider}")


async def extract_text(path: Path) -> str:
    parsed = parser.from_file(str(path))
    return parsed.get("content", "") or ""


async def get_texts_statistics(texts: List[str], model_name: str) -> Dict[str, Any]:
    enc = tiktoken.encoding_for_model(model_name)
    token_counts = [len(enc.encode(t)) for t in texts]
    lengths = [len(t) for t in texts]
    return {
        "subtexts": len(texts),
        "total_tokens_est": int(sum(token_counts) * 1.15),
        "total_chars": sum(lengths),
        "max_tokens": max(token_counts or [0]),
        "max_length": max(lengths or [0]),
    }


async def embed_texts(texts: List[str], config, meta_data: Dict[str, Any] | None = None) -> Tuple[bool, List[List[float]]]:
    token_limit = 8192
    meta_data = meta_data or {}
    client = await _build_client(config)
    model_name = (
        config.azure_settings.azure_openai_model_name
        if config.settings.ai_provider == AIProviders.AzureOpenAI
        else config.openai_settings.openai_model_name
    )
    texts = [t + json.dumps(meta_data) for t in texts]
    stats = await get_texts_statistics(texts, model_name)
    logger.debug("Embedding batch stats: {}", stats)
    if stats["total_tokens_est"] > token_limit:
        logger.info(f"Estimated tokens: {stats['total_tokens_est']} above limit of {token_limit}.")
        return False, []
    response = await client.embeddings.create(input=texts, model=model_name)
    embeddings = [d.embedding for d in response.data]
    logger.debug(f"Received {len(embeddings)} embeddings.")
    return True, embeddings
