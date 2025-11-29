import asyncio
import sys
import os
import signal
import tomllib
import click

from luxis.core.schemas import (
    Config,
    Directories,
    IngestConfig,
    QueryConfig,
    GeneralSettings,
    AzureOpenAISettings,
    OpenAISettings,
)
from luxis.services import update, query
from luxis.utils.logger import logger, setup_logging
from luxis.utils.pid_handler import read_pid
from luxis.daemon import run_daemon


def load_config(path: str | None):
    if not path:
        logger.info("No configuration specified, using defaults.")
        return Config()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    cfg_data = {}
    if "settings" in data:
        cfg_data["settings"] = GeneralSettings(**data["settings"])
    if "azure_settings" in data:
        cfg_data["azure_settings"] = AzureOpenAISettings(**data["azure_settings"])
    if "openai_settings" in data:
        cfg_data["openai_settings"] = OpenAISettings(**data["openai_settings"])
    if "ingest" in data:
        cfg_data["ingest"] = IngestConfig(**data["ingest"])
    if "query" in data:
        cfg_data["query"] = QueryConfig(**data["query"])
    if "directories" in data:
        cfg_data["directories"] = [Directories(**d) for d in data["directories"]]
    if "daemon" in data:
        from luxis.core.schemas import DaemonConfig

        cfg_data["daemon"] = DaemonConfig(**data["daemon"])
    return Config(**cfg_data)


@click.group(help="Luxis local indexing tool.")
def cli():
    pass


@cli.command(help="Start or stop the Luxis daemon service.")
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=False, dir_okay=False),
    help="Path to configuration TOML file (luxis.toml)",
)
@click.argument("action", type=click.Choice(["start", "stop"]))
def daemon(config_path, action):
    if action == "start":
        config = load_config(config_path)
        setup_logging(config.settings.log_level)
        run_daemon(config)
        sys.exit(0)

    if action == "stop":
        setup_logging()
        pid = asyncio.run(read_pid())
        if not pid:
            logger.error("Daemon PID not found.")
            sys.exit(1)
        try:
            os.kill(pid, signal.SIGTERM)
            logger.success(f"Stopped daemon process (PID {pid})")
        except ProcessLookupError:
            logger.warning("Daemon process not running.")
        sys.exit(0)


@cli.command(help="Scan and index files.")
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=False, dir_okay=False),
    help="Path to configuration TOML file (luxis.toml)",
)
def index(config_path):
    config = load_config(config_path)
    setup_logging(config.settings.log_level)
    asyncio.run(update.run_index_update(config))


@cli.command(help="Query the index with a text string.")
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=False, dir_okay=False),
    help="Path to configuration TOML file (luxis.toml)",
)
@click.argument("query_text", type=str)
def query_cmd(config_path, query_text):
    config = load_config(config_path)
    setup_logging(config.settings.log_level)
    asyncio.run(query.run_query(query_text, config))


def main():
    cli()


if __name__ == "__main__":
    main()
