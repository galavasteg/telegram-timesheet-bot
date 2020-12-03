from datetime import datetime


def parse_datetime(str_datetime: str) -> datetime:
    parsed = datetime.strptime(str_datetime.rsplit(".", 1)[0], "%Y-%m-%d %H:%M:%S")
    return parsed
