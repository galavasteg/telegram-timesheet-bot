"""
Read ENVs (parse .env file if "python-dotenv" installed),
prepare logger.

"""
import json
import logging.config
from os import getenv
from pathlib import Path

from .log_formatter import JSONFormatter
from utils import try_load_dotenv

this_dir = Path(__file__).parent

try_load_dotenv(this_dir / '.env')


PRJ_NAME = 'CheckYourTime'
DEBUG_MODE = getenv('DEBUG_MODE', 'false').lower() == 'true'

TELEGRAM_API_TOKEN = getenv('TELEGRAM_API_TOKEN', '')
assert TELEGRAM_API_TOKEN, 'TELEGRAM_API_TOKEN: Telegram bot API token not provided'

MAIN_LOG_NAME = PRJ_NAME.lower()
LOG_LEVEL = getenv('LOG_LEVEL', 'INFO')
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

access_ids_file = Path(getenv('ACCESS_IDS_FILE',
                              this_dir / 'allowed_accounts.json'))
assert access_ids_file.exists(), f'No such file: {access_ids_file=}'
with open(str(access_ids_file)) as f:
    ACCESS_IDS = set(json.load(f))


DB_NAME = 'database/timesheet.db'
DB_MIGRATIONS_DIR = 'database/migrations'
