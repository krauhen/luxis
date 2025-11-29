import sys
import tomllib
import click

from luxis.core.schemas import Config
from luxis.services import update, query
from luxis.utils.logger import logger


def load_config(path: str | None):
    if not path:
        logger.info("No configuration specified, using defaults.")
        return Config()
    try:
        with open(path, "rb") as f:
            config = tomllib.load(f)
            logger.info(f"Loaded configuration from {path}")
            config = Config(**config)
            return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        sys.exit(1)
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Invalid TOML syntax in {path}: {e}")
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
    ctx.obj["CONFIG"] = load_config(config_path)


@cli.command(help="Scan configured files, hash, embed, and update indices.")
@click.pass_context
def index(ctx):
    config = ctx.obj.get("CONFIG", {})
    update.run_index_update(config)


@cli.command(help="Query the index with a text string and show similar documents.")
@click.argument("query_text", type=str)
@click.pass_context
def query_cmd(ctx, query_text):
    config = ctx.obj.get("CONFIG", {})
    query.run_query(query_text, config)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
