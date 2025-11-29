import json
import os
import uuid

import luxis.daemon as daemon

from pathlib import Path

from luxis.core.schemas import Config, AIProviders
from luxis.utils.logger import logger


async def _user_config_path(user_id: uuid.UUID) -> Path:
    return daemon.CONFIG_DIR / f"{user_id}.json"


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
    path = daemon.CONFIG_DIR / f"{user_id}.json"
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
