"""JSON formatter.

Linter ignores.

N802 — Function name should be lowercase.
    Logging contract function names can be on snake-case style.
"""
import logging
import time
from typing import Optional

import ujson


class JSONFormatter(logging.Formatter):
    default_time_format = '%Y-%m-%d %H:%M:%S{ms} %z'
    msec_format = ',%03d'

    def __init__(self, *args, jsondumps_kwargs: Optional[dict] = None, **kwargs):
        """JSON format implementation of logging formatter."""
        super().__init__(*args, **kwargs)
        self._jsondumps_kwargs = jsondumps_kwargs.copy() if jsondumps_kwargs else {}

    def formatTime(self, record, *args) -> str:  # noqa: N802
        """Format TZ-time with milliseconds as this: 2020-10-09 11:26:07,080 +0300."""
        ct = self.converter(record.created)  # type: ignore
        formatted_ms = self.msec_format % record.msecs
        time_format_with_msec = self.default_time_format.format(ms=formatted_ms)

        formatted_time = time.strftime(time_format_with_msec, ct)
        return formatted_time

    def format(self, record: logging.LogRecord) -> str:
        r"""Serialize a log record to JSON.

        {"time": "2020-04-28 13:26:51,910", "name": "APPNAME", "lvl": "INFO",
         "msg": "input", "place": "module.func:105"}

        {"time": "2020-04-28 14:31:37,759", "name": "APPNAME", "lvl": "ERROR",
         "msg": "\"baz\" missed =/", "place": "logger_usage.main:14",
         "exc_info": "Traceback (most recent call last):\n  File \"/module.py\",
         line 12, in function\n .    _ = some_data['baz']\nKeyError: 'baz'"}.
        """
        record_representation = {
            'time': self.formatTime(record),
            'name': record.name,
            'lvl': record.levelname,
            'msg': record.getMessage(),
            'place': f'{record.module}.{record.funcName}:{record.lineno}',
        }

        if record.exc_info:
            exc_info = self.formatException(record.exc_info)
            record_representation['exc_info'] = exc_info

        return ujson.dumps(record_representation, **self._jsondumps_kwargs)
