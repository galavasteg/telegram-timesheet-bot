from datetime import datetime, timedelta


def parse_datetime(str_datetime: str) -> datetime:
    parsed = datetime.strptime(str_datetime.rsplit(".", 1)[0], "%Y-%m-%d %H:%M:%S")
    return parsed


def mm_ss_representation(seconds: int) -> str:
    return ':'.join(str(timedelta(seconds=seconds)).split(':')[1:])
