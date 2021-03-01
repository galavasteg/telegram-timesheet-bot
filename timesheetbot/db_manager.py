import sqlite3
from datetime import datetime, timedelta
from logging import getLogger
from pathlib import Path
from typing import Tuple, List
from uuid import uuid4 as uuid

from aiogram import types
from pypika import Table, SQLLiteQuery, Parameter, Order, Criterion

from settings.config import DB_NAME, DB_MIGRATIONS_DIR, DEBUG_MODE
from settings import constants
from timesheetbot.utils import parse_datetime

log = getLogger(__name__)

USER = Table('user')
CATEGORY = Table('category')
SESSION = Table('session')
TIMESHEET = Table('timesheet')


# TODO: Dataclasses for rows


class DoesNotExist(Exception):
    """Exception for empty DB-response."""


# TODO: postgres, db pool + pypika
class DBManager:

    def __init__(self):
        self._con = sqlite3.Connection(DB_NAME)
        if DEBUG_MODE:
            self._con.set_trace_callback(log.debug)
        self._cursor = self._con.cursor()

    def __del__(self):
        self._cursor.close()
        self._con.close()

    def _get_migration_file_paths(self) -> List[Path]:
        migrations_dir = Path(DB_MIGRATIONS_DIR)
        migrations = sorted(migrations_dir.glob('*'))
        return migrations

    def migrate(self) -> None:
        migration_paths = self._get_migration_file_paths()
        for migration_path in migration_paths:
            with migration_path.open('r', encoding='utf-8') as f:
                sql = f.read()
            self._cursor.executescript(sql)
            self._con.commit()

    def get_category(self, category_id: int) -> tuple:
        query = SQLLiteQuery.from_(CATEGORY).select('*') \
            .where(CATEGORY.id == Parameter(':category_id'))

        category = self._cursor.execute(
            query.get_sql(), {'category_id': category_id}).fetchone()

        if not category:
            raise DoesNotExist()

        return category

    def list_categories(self, u: types.User) -> Tuple[tuple]:
        """Get categories for current user"""
        query = SQLLiteQuery.from_(CATEGORY).select('*').where(CATEGORY.user_telegram_id.eq(u.id))
        categories = self._cursor.execute(query.get_sql())
        return tuple(categories)

    def get_user(self, u: types.User) -> tuple:
        query = SQLLiteQuery.from_(USER).select('*').where(
            USER.telegram_id.eq(u.id))

        db_user = self._cursor.execute(query.get_sql()).fetchone()
        if not db_user:
            raise DoesNotExist(query.get_sql())

        return db_user

    def register_user_if_not_exists(self, u: types.User) -> None:
        try:
            _ = self.get_user(u)
        except DoesNotExist:
            self.register_user(u)
            self.create_default_categories(u)

    def register_user(self, u: types.User) -> None:
        columns = 'telegram_id', 'interval_seconds', 'first_name', 'last_name', 'created_at'
        values = u.id, constants.DEFAULT_INTERVAL_SECONDS, u.first_name, u.last_name, str(datetime.now())
        column_value_map = dict(zip(columns, values))
        params = map(lambda col: f':{col}', columns)
        query = SQLLiteQuery.into(USER).columns(*columns).insert(
            *map(Parameter, params))

        _ = self._cursor.execute(query.get_sql(), column_value_map)
        self._con.commit()

    def create_default_categories(self, u: types.User) -> Tuple[Tuple[int, str]]:
        categories = tuple((u.id, category_name) for category_name in constants.DEFAULT_CATEGORIES)
        query = SQLLiteQuery.into(CATEGORY).columns(CATEGORY.user_telegram_id, CATEGORY.name).insert(*categories)

        _ = self._cursor.execute(query.get_sql())
        self._con.commit()

        return categories

    def create_session(self, u: types.User):
        columns = 'user_telegram_id', 'start_at'
        values = u.id, str(datetime.now())
        column_value_map = dict(zip(columns, values))
        params = map(lambda col: f':{col}', columns)
        query = SQLLiteQuery.into(SESSION).columns(*columns).insert(
            *map(Parameter, params))

        _ = self._cursor.execute(query.get_sql(), column_value_map)
        self._con.commit()

        created_session_id = self._cursor.lastrowid
        return created_session_id

    def get_new_or_existing_session_id(self, u: types.User) -> Tuple[int, bool]:
        try:
            existing_session = self._get_active_session(u)
        except DoesNotExist:
            new_session_id = self.create_session(u)
            return new_session_id, True
        else:
            return existing_session[0], False

    def get_last_started_session(self, u: types.User) -> Tuple:
        query = SQLLiteQuery().from_(SESSION).select('*') \
            .where(SESSION.user_telegram_id.eq(Parameter(':user_id'))) \
            .orderby(SESSION.start_at, order=Order.desc) \
            .limit(1).get_sql()

        session = self._cursor.execute(query, {'user_id': u.id}).fetchone()

        if not session:
            raise DoesNotExist()

        session = (*session[:-2], *map(parse_datetime, session[-2:-1]), session[-1])
        return session

    def try_stop_session(self, u: types.User) -> bool:
        """Return True if session stopped or False otherwise
        that means that there is no active session to stop"""
        try:
            opened_session = self._get_active_session(u)
        except DoesNotExist:
            return False
        else:
            session_id, *_ = opened_session
            query = SQLLiteQuery.update(SESSION) \
                .set(SESSION.stop_at, Parameter(':stop_at')) \
                .where(SESSION.id.eq(session_id))
            self._cursor.execute(query.get_sql(), {'stop_at': datetime.now()})
            self._con.commit()
            return True

    def get_unstopped_activity(self, activity_id: str) -> tuple:
        column_value_map = {'activity_id': activity_id}
        query = SQLLiteQuery.from_(TIMESHEET).select('*').where(
            (TIMESHEET.activity_id == Parameter(':activity_id')) &
            (TIMESHEET.default_category_id.isnull()) &
            (TIMESHEET.user_category_id.isnull())
        )

        activity = self._cursor.execute(query.get_sql(), column_value_map).fetchone()
        if not activity:
            raise DoesNotExist()

        return activity

    def stop_activity(self, activity_id: str, category_id: int):
        _ = self.get_unstopped_activity(activity_id)  # check existing

        column_value_map = {'activity_id': activity_id}
        query = SQLLiteQuery.update(TIMESHEET).set(TIMESHEET.default_category_id, category_id).where(
            TIMESHEET.activity_id == Parameter(':activity_id'))

        self._cursor.execute(query.get_sql(), column_value_map)
        self._con.commit()

        if self._cursor.rowcount > 1:
            raise RuntimeError()

    def start_activity(self, session_id: int, interval_seconds: int) -> str:
        finish = datetime.now()
        start = finish - timedelta(0, interval_seconds)
        columns = 'activity_id', 'session_id', 'start', 'finish'
        values = str(uuid()), session_id, str(start), str(finish)
        column_value_map = dict(zip(columns, values))
        params = map(lambda col: f':{col}', columns)
        query = SQLLiteQuery.into(TIMESHEET).columns(*columns).insert(
            *map(Parameter, params))

        _ = self._cursor.execute(query.get_sql(), column_value_map)
        self._con.commit()

        return column_value_map['activity_id']

    def set_interval_seconds(self, u: types.User, interval_seconds: int) -> int:
        query = SQLLiteQuery.update(USER) \
            .set(USER.interval_seconds, interval_seconds) \
            .where(USER.telegram_id.eq(u.id))

        _ = self._cursor.execute(query.get_sql())
        self._con.commit()

        return self._cursor.rowcount

    def get_interval_seconds(self, u: types.User) -> int:
        db_user = self.get_user(u)
        # TODO dataclass?
        interval = db_user[1]
        return interval

    def has_active_session(self, u: types.User) -> bool:
        try:
            self._get_active_session(u)
            return True
        except DoesNotExist:
            return False

    def _get_active_session(self, u: types.User) -> tuple:
        query = SQLLiteQuery.from_(SESSION).select(SESSION.id) \
            .where(SESSION.user_telegram_id.eq(u.id)) \
            .where(SESSION.stop_at.isnull())

        session = self._cursor.execute(query.get_sql()).fetchone()
        if not session:
            raise DoesNotExist(query.get_sql())

        return session

    def get_timesheet_frame_by_sessions(self, session_ids: tuple) -> List[tuple]:
        if not session_ids:
            raise DoesNotExist()

        query = f"""
        SELECT ts.*, cat.name
        FROM {TIMESHEET} ts
        JOIN {CATEGORY} cat ON ts.default_category_id is not null AND ts.default_category_id = cat.id
        WHERE ts.session_id in ({','.join(map(str, session_ids))})
        ORDER BY ts.start
        """

        timesheet_frame = self._cursor.execute(query).fetchall()

        if not timesheet_frame:
            raise DoesNotExist()

        return timesheet_frame

    def filter_user_sessions_by_start(self, u: types.User, start: datetime) -> List[tuple]:
        params = {'t0': start, ':user_id': u.id}
        query = 'SELECT * FROM session WHERE user_telegram_id = :user_id AND :t0 <= start_at'

        sessions_frame = self._cursor.execute(query, params).fetchall()

        if not sessions_frame:
            raise DoesNotExist()

        return sessions_frame

    def get_user_unfilled_activities(self, u: types.User) -> List[tuple]:
        query = '''
            select a.*
            from timesheet a
                join session s on s.id = a.session_id
                    -- and s.category_id = :user_id
                    and s.user_telegram_id = :user_id
            where default_category_id is null
        '''

        unfilled_activities = self._cursor.execute(query, {'user_id': u.id}).fetchall()

        if not unfilled_activities:
            raise DoesNotExist()

        return unfilled_activities
