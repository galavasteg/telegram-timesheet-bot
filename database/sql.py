CREATE_TABLES = [
    """CREATE TABLE IF NOT EXISTS user (
            telegram_id integer,
            name string,
            last_name string,
            created_at datetime);
    """,
    """
    CREATE TABLE IF NOT EXISTS category (
        id integer PRIMARY KEY AUTOINCREMENT,
        user_telegram_id integer,
        name string);""",
    """
    CREATE TABLE IF NOT EXISTS default_category (
        id integer PRIMARY KEY AUTOINCREMENT,
        name string UNIQUE);""",
    """
    CREATE TABLE IF NOT EXISTS timesheet (
        uuid string PRIMARY KEY,
        session_id integer,
        user_category_id integer,
        default_category_id integer,
        start datetime,
        finish datetime);""",
    """
    CREATE TABLE IF NOT EXISTS session (
        id integer PRIMARY KEY AUTOINCREMENT,
        user_telegram_id integer,
        time_interval integer,
        session_start datetime,
        session_stop datetime);"""
]

CATEGORY_INSERTS = [
    "INSERT OR IGNORE INTO default_category(name) VALUES ('Работа')",
    "INSERT OR IGNORE INTO default_category(name) VALUES ('TimeKiller')",
    "INSERT OR IGNORE INTO default_category(name) VALUES ('Еда')",
    "INSERT OR IGNORE INTO default_category(name) VALUES ('Гулять')",
    "INSERT OR IGNORE INTO default_category(name) VALUES ('Тренировка')",
    "INSERT OR IGNORE INTO default_category(name) VALUES ('Сон')",
]