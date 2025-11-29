import sys
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


def load_config(path: str | None):
    if not path:
        logger.info("No configuration specified, using defaults.")
        return Config()

    try:
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

            config = Config(**cfg_data)
            logger.info(f"Loaded configuration from {path}")
            return config

    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        sys.exit(1)
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Invalid TOML syntax: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)


@click.group(help="Luxis local indexing tool.")
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=False, dir_okay=False),
    help="Path to configuration TOML file (luxis.toml)",
)
@click.pass_context
def cli(ctx, config_path):
    ctx.ensure_object(dict)
    config = load_config(config_path)
    setup_logging(config.settings.log_level)
    ctx.obj["CONFIG"] = load_config(config_path)


@cli.command(help="Scan and index files.")
@click.pass_context
def index(ctx):
    update.run_index_update(ctx.obj["CONFIG"])


@cli.command(help="Query the index with a text string.")
@click.argument("query_text", type=str)
@click.pass_context
def query_cmd(ctx, query_text):
    query.run_query(query_text, ctx.obj["CONFIG"])


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
