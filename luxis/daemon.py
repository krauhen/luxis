import asyncio
import uvicorn

from pathlib import Path
from fastapi import FastAPI
from starlette.responses import JSONResponse
from urllib.request import Request

from luxis.core.schemas import Config
from luxis.utils.exceptions import log_exception
from luxis.utils.logger import logger
from luxis.utils.pid_handler import write_pid
from luxis.api.endpoints import router as endpoint_router

BASE_CONFIG: Config | None = None
CONFIG_DIR: Path | None = None

app = FastAPI()
app.include_router(endpoint_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    await log_exception(exc, context="UnhandledExceptionHandler")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


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
