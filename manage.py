import platform
from logging import config as logging_config

import click
from aiogram.utils import executor

from settings import LOG_CONFIG


@click.group()
def cli():
    logging_config.dictConfig(LOG_CONFIG)

    if platform.system() != 'Windows':
        import uvloop
        uvloop.install()


@cli.command(short_help='start bot')
def start():
    """Start the bot."""


if __name__ == '__main__':
    cli()
