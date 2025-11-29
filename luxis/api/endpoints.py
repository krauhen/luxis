import asyncio
import uuid

import luxis.daemon as daemon

from fastapi import Query, Body, Security, Depends, APIRouter
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, SecretStr, Field
from typing import Tuple, List

from luxis.core.schemas import AIProviders, QueryConfig, Directories
from luxis.services import update, query
from luxis.utils.daemon import _load_or_create_user_config, _replace_api_key_in_config
from luxis.utils.logger import logger

router = APIRouter()


api_key_scheme = APIKeyHeader(
    name="api-key",
    scheme_name="api-key",
    description="Standard API key for identifying the client.",
)


class IndexRequest(BaseModel):
    directories: List[Directories] = Field(default_factory=lambda: [Directories()], description="Directories list")


class QueryRequest(BaseModel):
    texts: list[str]
    query_config: QueryConfig = Field(default=QueryConfig(), description="Query configuration")


async def get_api_key(
    api_key: str = Security(api_key_scheme),
) -> Tuple[SecretStr, AIProviders]:
    if not api_key:
        raise Exception("Missing required header: api-key")

    key = api_key.strip()

    if len(key) > 100:
        ai_provider = AIProviders.OpenAI
    elif 10 < len(key) < 100:
        ai_provider = AIProviders.AzureOpenAI
    else:
        raise Exception("Unknown or unsupported key type")

    logger.debug(f'Got "api-key" of provider {ai_provider}')
    return SecretStr(api_key), ai_provider


@router.post("/ingest")
async def ingest_endpoint(
    user_id: uuid.UUID = Query(...),
    invalidate_config: bool = Query(False),
    clean_index: bool = Query(False),
    verbose: bool = Query(False),
    body: IndexRequest = Body(...),
    api_key_info: Tuple[SecretStr, AIProviders] = Depends(get_api_key),
):
    cfg = await _load_or_create_user_config(daemon.BASE_CONFIG, user_id, invalidate_config)
    cfg = await _replace_api_key_in_config(cfg, api_key_info)
    cfg.directories = body.directories

    start = asyncio.get_event_loop().time()
    response = await update.run_index_update(cfg, clean_index)
    elapsed = asyncio.get_event_loop().time() - start
    if verbose:
        response["elapsed"] = elapsed
        return response
    else:
        return {"status": "success"}


@router.post("/query")
async def query_endpoint(
    user_id: uuid.UUID = Query(...),
    body: QueryRequest = Body(...),
    api_key_info: Tuple[SecretStr, AIProviders] = Depends(get_api_key),
):
    cfg = await _load_or_create_user_config(daemon.BASE_CONFIG, user_id, False)
    cfg = await _replace_api_key_in_config(cfg, api_key_info)
    cfg.query = body.query_config

    results_all = []
    for text in body.texts:
        results = []
        entries = await query.run_query(text, cfg)
        logger.info(f"Found {len(entries)} entries")
        if entries:
            results.extend(entries)
        results_all.append(results)
    return {"status": "success", "results": results_all}
