import json
from pathlib import Path

from envparse import Env


this_dir = Path(__file__).parent

env = Env()
env.read_envfile()

DEBUG_MODE = env.bool('DEBUG_MODE', default=True)
LOG_LEVEL = env('LOG_LEVEL', default='INFO').upper()
TELEGRAM_API_TOKEN = env.str('TELEGRAM_API_TOKEN', default='')
ACCESS_IDS_FILE = Path(env.str('ACCESS_IDS_FILE', default=str(this_dir / 'allowed_accounts.json')))

DB_NAME = 'database/timesheet.db'
DB_MIGRATIONS_DIR = 'migrations'
