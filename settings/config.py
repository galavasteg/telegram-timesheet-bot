import json
from pathlib import Path

from envparse import Env


this_dir = Path(__file__).parent

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
