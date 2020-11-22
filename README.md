# [CheckYourTime](http://t.me/checkyourtime_bot) - Telegram bot to track the time of your activities

**CheckYourTime** - Telegram бот для учёта личного времени на отрезках 15-30 мин.
Вдохновлением для этого проекта стала [статья](https://vc.ru/life/143273-12-mesyacev-vedu-pochasovoy-uchet-svoih-del-s-pomoshchyu-timesheets-rasskazyvayu-k-chemu-eto-v-itoge-privelo)
Павла Домрачева и идея сделать бота от участников клуба.

## Contents

- [Features](#features)
- [Install](#install)
- [Running](#running)
    - [Reading .env file](#reading-env-file)
- [TODO](#todo)
- [License](#license)

## Features

- Default groups: `Работа`, `TimeKiller`, `Еда`, `Прогулка`, `Тренировка`, `Сон`,
- 

## Install
0. Установить последнюю версию [python](https://www.python.org/downloads/) и [git](https://git-scm.com/downloads).
1. С терминале, на уровне папки, куда хотите расместить файлы проекта, выполнить:
 
    `git clone https://github.com/galavasteg/telegram-timesheet-bot.git`

3. Необязательно, но желательно настроить и активировать виртуальное окружение по, например, [этой инструкции](https://python-scripts.com/virtualenv).
4. В терминале в директории проекта последовательно выполнить установку зависимостей:
    
    `python -m pip install --upgrade pip setuptools`
    
    `python -m pip install -r requirements.txt`

## Before Running
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

### Read '.env' file
NOTE. В корень проекта можно поместить файл `.env`, чтобы переменные окружения читаль из него.
На сервере так делать не стоит.
WARNING: '.env' файл НЕ хранить в репозитории проекта.
```
# .env
TELEGRAM_API_TOKEN = secret
DEBUG_MODE = true
LOG_LEVEL = info
```

## TODO
- clean and upgrade dependencies
- Makefile for installation and running
- use 'envparse'?
- use 'click' in manage.py (create it)
- create services.py for business logic, 'application' directory for other stuff
- configure everything in manage.py
- tests =)
- migrate to postgres and use 'asyncpg'
- docker-compose.yaml
- timezone
- internationalization

## License

MIT licensed. See the
[LICENSE](https://github.com/sloria/environs/blob/master/LICENSE) file
for more details.