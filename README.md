# [CheckYourTime](http://t.me/checkyourtime_bot) - Telegram bot to track the time of your activities

**CheckYourTime** - Telegram бот для учёта личного времени на отрезках 15-30 мин.
Вдохновлением для этого проекта стала [статья](https://vc.ru/life/143273-12-mesyacev-vedu-pochasovoy-uchet-svoih-del-s-pomoshchyu-timesheets-rasskazyvayu-k-chemu-eto-v-itoge-privelo)
Павла Домрачева и идея сделать бота от участников [клуба](https://titanman.ru/).


- [1. Features](#1-features)
- [2. Install](#2-install)
- [3. Running](#3-before-running)
    - [3.1. Before running](#3-1-before-running)
    - [3.2. Reading .env file](#3-2-reading-env-file)
    - [3.3. Run bot server](#3-3-run-bot-server)
- [4. Database](#4-database)
- [TODO](#todo)
- [License](#license)

## 1. Features

- Default categories: `Работа`, `TimeKiller`, `Еда`, `Прогулка`, `Тренировка`, `Сон`
- Statistics for the `last 24 hours`, `last session`, `week`, `month`
- Intervals: `15 min`, `20 min`, `30 min`
    - additional [debug](#3-1-before-running)-intervals: `5 sec`, `10 sec`, `30 sec`


## 2. Install
0. Установить последнюю версию [python](https://www.python.org/downloads/) и [git](https://git-scm.com/downloads).
1. С терминале, на уровне папки, куда хотите расместить файлы проекта, выполнить:
 
    `git clone https://github.com/galavasteg/telegram-timesheet-bot.git`

3. Необязательно, но желательно настроить и активировать виртуальное окружение по, например, [этой инструкции](https://python-scripts.com/virtualenv).
4. В терминале в директории проекта последовательно выполнить установку зависимостей:
    
    `python -m pip install --upgrade pip setuptools`
    
    `python -m pip install -r requirements.txt`


## 3. Running
TLDR Для запуска сервера бота выполнить в терминале:

`python server.py`

### 3.1. Before Running
Для начала, необходимо указать следующие переменные окружения:
```
TELEGRAM_API_TOKEN = your_bot_secret_token
ACCESS_IDS_FILE = white_list_of_tg_accounts
```
`ACCESS_IDS_FILE` — Путь к файлу со списком ID Telegram аккаунтов, от которых будут приниматься
сообщения (сообщения от остальных аккаунтов игнорируются).
Если файл содержит пустой список, то будут обрабатываться сообщения от всех пользователей. Формат файла:
```
# allowed_accounts.json
[
  12345678,
  23456789,
  34567890
]
```

Дополнительные переменные окружения:
```
# 'false' by default
DEBUG_MODE = true|false
# 'info' by default
LOG_LEVEL = debug|info|error|critical
```

### 3.2. Read '.env' file
NOTE. В корень проекта можно поместить файл `.env`, чтобы переменные окружения читаль из него.
На сервере так делать не стоит.

WARNING: `.env` файл НЕ хранить в репозитории проекта.
```
# .env
TELEGRAM_API_TOKEN = secret
DEBUG_MODE = true
LOG_LEVEL = info
```


## 4. Database
Используется файловая СУБД SQLite3.

В будущем планируется использование postgresql и библиотеки `asyncpg`, т.к. само приложение асинхронное.


## TODO
### bugfix
- latency on start or receiving messages from bot
- [not confirmed] missing or lost categories in statistics

### refactoring
- Bot Version.
- clean and upgrade dependencies
- linter [wemake-python-styleguide](https://wemake-python-stylegui.de/en/latest/)
- Makefile for installation and running
- use 'envparse'?
- use 'click' in manage.py (create it)
- create services.py for business logic, 'application' directory for other stuff
- configure everything: logger, db conn pool, sync, etc. - in manage.py
- messages refactoring
- EN readme
- tests =)
- migrate to postgresql and use 'asyncpg'
- docker-compose.yaml

### features
- ask user set interval before start new session
- notify user about not completed activities
- adding user's custom categories
- on/off user categories
- statistics: excel representation
- timezone
- internationalization


## License
BSD licensed. See the
[LICENSE](https://github.com/galavasteg/telegram-timesheet-bot/blob/master/LICENSE) file
for more details.