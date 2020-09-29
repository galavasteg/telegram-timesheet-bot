import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4 as uuid

from settings.config import DB_NAME, DB_MIGRATIONS_DIR


class DBManager:

    def __init__(self):
        self._con = sqlite3.Connection(DB_NAME)
        self._cursor = self._con.cursor()

    def _get_migration_file_paths(self):
        migrations_dir = Path(DB_MIGRATIONS_DIR)
        migrations = sorted(migrations_dir.glob('*'))
        return migrations

    def migrate(self):
        migration_paths = self._get_migration_file_paths()
        for migration_path in migration_paths:
            with migration_path.open('r', encoding='utf-8') as f:
                sql = f.read()
            self._cursor.executescript(sql)
            self._con.commit()

    def list_categories(self):
        categories = self._cursor.execute('SELECT name FROM default_category')
        result_list = ''

        # TODO: representation not on this level
        for category in categories:
            result_list += 'Категория ' + str(category) + '\n'

        return result_list

    def try_register_user(self, user):
        query = f'SELECT * FROM user WHERE telegram_id = {user.id}'
        db_user = self._cursor.execute(query).fetchone()

        if not db_user:
            self.register_user(user)

    def register_user(self, user):
        quary = f'INSERT INTO user(telegram_id, name, last_name, created_at)' \
                f'VALUES ({user.id}, {user.first_name}, {user.last_name}, {datetime.now()})'
        self._cursor.execute(quary)
        self._con.commit()

    def try_start_session(self, user_id, start_date):
        existing_session = self._get_active_session_id_for_user(user_id)

        if existing_session.fetchone() == None:

            default_interval = 20 * 60
            previous_interval = self._cursor.execute('SELECT time_interval FROM session WHERE id = (SELECT MAX(id) from session WHERE user_telegram_id = :user_telegram_id)',
                                                 {'user_telegram_id': user_id}).fetchone()
            if previous_interval is None:
                previous_interval = default_interval
            else:
                previous_interval = previous_interval[0]

            self._cursor.execute(
                'INSERT INTO session(user_telegram_id, time_interval, session_start) VALUES (:user_telegram_id, :time_interval, :session_start)',
                {'user_telegram_id': user_id,
                 'time_interval': previous_interval,
                 'session_start': start_date})
            self._con.commit()
            return True
        else:
            return False

    def try_stop_session(self, user_id, stop_date):
        existing_session = self._get_active_session_id_for_user(user_id)

        fetched = existing_session.fetchone()
        if fetched is not None:
            self._cursor.execute(
                'UPDATE session SET session_stop = :session_stop where id = :id',
                {'session_stop': stop_date,
                 'id': fetched[0]})
            self._con.commit()
            return True
        else:
            return False

    def try_stop_event(self, user_id, category, start_date):
        query = f"""
            UPDATE timesheet
            SET finish = datetime(strftime('%s', start) + 
                                  (select time_interval from session where session_id = id),
                                  'unixepoch'),
                default_category_id = (select id from category 
                                       where user_telegram_id = {user_id} and name = '{category}'),
                user_category_id = (select id from default_category where name = '{category}')
            WHERE uuid IN (SELECT uuid 
                           FROM timesheet tm
                            JOIN session s on tm.session_id = s.id
                           WHERE s.user_telegram_id = {user_id}
                            AND tm.start = '{start_date}'
                            AND tm.finish is NULL)"""
        stopped_event = self._cursor.execute(query)
        self._con.commit()

        stopped = stopped_event.rowcount == 1
        return stopped

    def start_event(self, user_id, start_date):
        session_id = self._get_active_session_id_for_user(user_id).fetchone()[0]
        query = f"""INSERT INTO timesheet(uuid, session_id, start)
                VALUES  ('{str(uuid())}', {session_id}, '{start_date}')"""
        _ = self._cursor.execute(query)
        self._con.commit()

    def try_set_step(self, user_id, step):
        session_id = self._get_active_session_id_for_user(user_id).fetchone()
        if session_id is None:
            return False

        session_id = session_id[0]

        query = f"""UPDATE session
                SET time_interval = {step}
                WHERE id = {session_id}"""
        res = self._cursor.execute(query)
        self._con.commit()

        return True

    def try_get_step(self, user_id):
        session_id = self._get_active_session_id_for_user(user_id).fetchone()
        if session_id is None:
            return False, None

        session_id = session_id[0]

        step = self._cursor.execute(
            """SELECT time_interval
                FROM session
                WHERE id = :session_id""",
            {'session_id': session_id}).fetchone()[0]

        return True, step

    def _get_active_session_id_for_user(self, user_id):
        query = f'SELECT id FROM session' \
                f'WHERE user_telegram_id = {user_id} AND session_stop is NULL'
        return self._cursor.execute(query)
