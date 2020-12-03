"""
Read ENVs (parse .env file if "python-dotenv" installed),
prepare logger.

"""
import json
import logging.config
from pathlib import Path

from envparse import Env

from .log_formatter import JSONFormatter


this_dir = Path(__file__).parent

PRJ_NAME = 'CheckYourTime'

env = Env()
env.read_envfile()

DEBUG_MODE = env.bool('DEBUG_MODE', default=True)
LOG_LEVEL = env('LOG_LEVEL', default='INFO').upper()
TELEGRAM_API_TOKEN = env.str('TELEGRAM_API_TOKEN')

assert TELEGRAM_API_TOKEN, 'TELEGRAM_API_TOKEN not provided.'

access_ids_file = Path(env.str('ACCESS_IDS_FILE', default=str(this_dir / 'allowed_accounts.json')))
assert access_ids_file.exists(), f'No such file: {access_ids_file=}'
with access_ids_file.open(encoding='utf-8') as f:
    ACCESS_IDS = set(json.load(f))

DB_NAME = 'database/timesheet.db'
DB_MIGRATIONS_DIR = 'database/migrations'

MAIN_LOG_NAME = PRJ_NAME.lower()
log_conf = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': JSONFormatter,
            'jsondumps_kwargs': {
                'ensure_ascii': False,
                # 'indent': 2,
            }
        }
    },
    'handlers': {
        'json2console': {
          'class': 'logging.StreamHandler',
          'level': LOG_LEVEL,
          'formatter': 'json',
          'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        MAIN_LOG_NAME: {
            'level': LOG_LEVEL,
            'handlers': [
                'json2console',
            ],
            'propagate': False,
        },
    }
}
logging.config.dictConfig(log_conf)
LOG = logging.getLogger(MAIN_LOG_NAME)
