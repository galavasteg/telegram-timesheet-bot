CREATE TABLE IF NOT EXISTS user (
    telegram_id integer PRIMARY KEY,
    interval_seconds integer,
    first_name string,
    last_name string,
    created_at datetime
);

CREATE TABLE IF NOT EXISTS category (
    id integer PRIMARY KEY AUTOINCREMENT,
    user_telegram_id integer,
    name varchar(255)
);

CREATE TABLE IF NOT EXISTS default_category (
    id integer PRIMARY KEY AUTOINCREMENT,
    name string UNIQUE
);

CREATE TABLE IF NOT EXISTS timesheet (
    activity_id varchar(255) PRIMARY KEY,
    session_id integer,
    user_category_id integer,
    default_category_id integer,
    start datetime,
    finish datetime
);

CREATE TABLE IF NOT EXISTS session (
    id integer PRIMARY KEY AUTOINCREMENT,
    user_telegram_id integer,
    start_at datetime,
    stop_at datetime
);
