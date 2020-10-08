import os
from datetime import datetime
from typing import Union, Text


def try_load_dotenv(directory: Union[Text, os.PathLike, None]) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # dotenv doesn't installed on PRD
        pass
    else:
        load_dotenv(directory)


def parse_datetime(str_datetime: str) -> datetime:
    parsed = datetime.strptime(str_datetime.rsplit(".", 1)[0], "%Y-%d-%m %H:%M:%S")
    return parsed
