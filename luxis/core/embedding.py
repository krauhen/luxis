import json
import tiktoken

from pathlib import Path
from typing import Any, Dict, List, Tuple
from openai import AsyncAzureOpenAI
from tika import parser

from luxis.utils.settings import settings
from luxis.utils.logger import logger


client = AsyncAzureOpenAI(
    api_key=settings.azure_openai_api_key.get_secret_value(),
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint,
    azure_deployment=settings.azure_openai_deployment,
)


def extract_text(path: Path) -> str:
    parsed = parser.from_file(str(path))
    return parsed.get("content", "") or ""


async def get_texts_statistics(texts: List[str]) -> Dict[str, Any]:
    enc = tiktoken.encoding_for_model(settings.azure_openai_model_name)
    token_counts = [len(enc.encode(t)) for t in texts]
    lengths = [len(t) for t in texts]
    return {
        "subtexts": len(texts),
        "total_tokens_est": int(sum(token_counts) * 1.15),
        "total_chars": sum(lengths),
        "max_tokens": max(token_counts or [0]),
        "max_length": max(lengths or [0]),
    }


async def embed_texts(texts: List[str], meta_data: Dict[str, Any] | None = None) -> Tuple[bool, List[List[float]]]:
    meta_data = meta_data or {}
    texts = [t + json.dumps(meta_data) for t in texts]

    stats = await get_texts_statistics(texts)
    logger.debug("Embedding batch stats: {}", stats)

    if stats["total_tokens_est"] > 8192:
        return False, []

    response = await client.embeddings.create(input=texts, model=settings.azure_openai_model_name)

    if hasattr(response, "usage") and response.usage:
        logger.debug(f"Token usage: {response.usage.total_tokens}")

    embeddings = [d.embedding for d in response.data]
    logger.debug(f"Received {len(embeddings)} embeddings.")
    return True, embeddings
