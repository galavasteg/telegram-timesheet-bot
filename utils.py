import os
from typing import Union, Text


def try_load_dotenv(directory: Union[Text, os.PathLike, None]) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # dotenv doesn't installed on PRD
        pass
    else:
        load_dotenv(directory)
