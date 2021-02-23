import platform
from logging import config as logging_config

import click
from aiogram.utils import executor

from settings import LOG_CONFIG
from timesheetbot.db_manager import DBManager
from timesheetbot.server import dp


@click.group()
def cli():
    logging_config.dictConfig(LOG_CONFIG)

    if platform.system() != 'Windows':
        import uvloop
        uvloop.install()


@cli.command(short_help='apply db migrations')
def migrate():
    database = DBManager()
    database.migrate()


@cli.command(short_help='start bot')
def start():
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    cli()
