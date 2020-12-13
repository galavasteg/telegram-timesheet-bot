from .config import LOG_LEVEL
from .log_formatter import JSONFormatter

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'timesheetbot': {
            'level': LOG_LEVEL,
            'handlers': [
                'json2console',
            ],
            'propagate': False,
        }
    },
    'handlers': {
        'json2console': {
          'class': 'logging.StreamHandler',
          'formatter': 'json',
          'stream': 'ext://sys.stdout'
        },
    },
    'formatters': {
        'json': {
            '()': JSONFormatter,
            'jsondumps_kwargs': {
                'ensure_ascii': False,
                # 'indent': 2,
            }
        }
    },
}
