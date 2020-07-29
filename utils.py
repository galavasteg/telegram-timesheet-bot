from pathlib import Path


def try_load_dotenv(directory: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # dotenv doesn't installed on PRD
        pass
    else:
        load_dotenv(directory)
