import asyncio
import json
import os
import uuid
import uvicorn

from pathlib import Path
from fastapi import FastAPI, Query, Body, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, SecretStr
from starlette.responses import JSONResponse
from typing import Tuple
from urllib.request import Request

from luxis.core.schemas import Config, AIProviders
from luxis.services import update, query
from luxis.utils.exceptions import log_exception
from luxis.utils.logger import logger
from luxis.utils.pid_handler import write_pid

BASE_CONFIG: Config | None = None
CONFIG_DIR: Path | None = None


app = FastAPI()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    await log_exception(exc, context="UnhandledExceptionHandler")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


api_key_scheme = APIKeyHeader(
    name="api-key",
    scheme_name="api-key",
    description="Standard API key for identifying the client.",
)


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


class QueryRequest(BaseModel):
    texts: list[str]


async def _user_config_path(user_id: uuid.UUID) -> Path:
    return CONFIG_DIR / f"{user_id}.json"


async def _remove_user_config(user_id):
    os.remove(await _user_config_path(user_id))


def _build_user_paths(base_config: Config, user_id: uuid.UUID) -> Config:
    cfg = base_config.model_copy(deep=True)
    base_dir = Path(base_config.daemon.base_data_dir)
    user_dir = base_dir / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    cfg.settings.vector_index_path = str(user_dir / "vector_index.faiss")
    cfg.settings.meta_index_path = str(user_dir / "meta_index.db")
    return cfg


async def _load_or_create_user_config(base_config: Config, user_id: uuid.UUID, invalidate_config: bool) -> Config:
    path = await _user_config_path(user_id)
    if path.exists() and not invalidate_config:
        logger.info(f"Loading user config for user {user_id}")
        data = json.loads(path.read_text())
        return Config.model_validate(data)
    elif invalidate_config:
        logger.info(f"Invalidating config for user {user_id}")
        if path.exists():
            await _remove_user_config(user_id)
    else:
        logger.info(f"Found no user config for user {user_id}, will create a new one.")
    cfg = _build_user_paths(base_config, user_id)
    path.write_text(cfg.model_dump_json(indent=2))
    return cfg


async def _replace_api_key_in_config(cfg, api_key_info):
    api_key, ai_provider = api_key_info
    if ai_provider != cfg.settings.ai_provider:
        raise Exception("Invalid API Key.")
    elif ai_provider == AIProviders.AzureOpenAI:
        cfg.azure_settings.azure_openai_api_key = api_key
    elif ai_provider == AIProviders.OpenAI:
        cfg.openai_settings.openai_api_key = api_key
    else:
        logger.error(f"Unknown AIProvider: {ai_provider}")
    return cfg


@app.get("/ingest")
async def ingest_endpoint(
    user_id: uuid.UUID = Query(...),
    invalidate_config: bool = Query(False),
    clean_index: bool = Query(False),
    verbose: bool = Query(False),
    api_key_info: Tuple[SecretStr, AIProviders] = Depends(get_api_key),
):
    cfg = await _load_or_create_user_config(BASE_CONFIG, user_id, invalidate_config)
    cfg = await _replace_api_key_in_config(cfg, api_key_info)

    start = asyncio.get_event_loop().time()
    response = await update.run_index_update(cfg, clean_index)
    elapsed = asyncio.get_event_loop().time() - start
    if verbose:
        response["elapsed"] = elapsed
        return response
    else:
        return {"status": "success"}


@app.post("/query")
async def query_endpoint(
    user_id: uuid.UUID = Query(...),
    body: QueryRequest = Body(...),
    api_key_info: Tuple[SecretStr, AIProviders] = Depends(get_api_key),
):
    cfg = await _load_or_create_user_config(BASE_CONFIG, user_id, False)
    cfg = await _replace_api_key_in_config(cfg, api_key_info)

    results_all = []
    for text in body.texts:
        results = []
        entries = await query.run_query(text, cfg)
        logger.info(f"Found {len(entries)} entries")
        if entries:
            results.extend(entries)
        results_all.append(results)
    return {"status": "success", "results": results_all}


def run_daemon(config: Config):
    global BASE_CONFIG, CONFIG_DIR
    BASE_CONFIG = config
    CONFIG_DIR = Path(config.daemon.base_data_dir) / "configs"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    asyncio.run(write_pid())
    logger.info(f"Luxis daemon running on {config.daemon.host}:{config.daemon.port}")
    uvicorn.run(
        app,
        host=config.daemon.host,
        port=config.daemon.port,
        reload=config.daemon.reload,
        timeout_keep_alive=config.daemon.shutdown_timeout,
    )
