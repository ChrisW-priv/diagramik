import os
import datetime as dt
import json
import logging
from typing import override


LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class MyJSONFormatter(logging.Formatter):
    def __init__(self, *, kwargs: dict[str, str] | None = None):
        super().__init__()
        self.kwargs = kwargs if kwargs is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.kwargs.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message


class NonErrorFilter(logging.Filter):
    """
    Returns only messages that are Debug or Info.
    Used to print debug and info to stdout and rest to stderr.
    """

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= logging.INFO


formatters = {
    "simple": {
        "format": "[%(levelname)s] %(asctime)s: %(message)s",
        "datefmt": "%Y-%m-%dT%H:%M:%S%z",
    },
    "json": {
        "()": MyJSONFormatter,
        "kwargs": {
            "level": "levelname",
            "message": "message",
            "timestamp": "timestamp",
            "logger": "name",
            "module": "module",
            "function": "funcName",
            "line": "lineno",
            "thread_name": "threadName",
        },
    },
}

filters = {
    "no_error": {
        "()": NonErrorFilter,
    }
}

stdout_handler = {
    "class": "logging.StreamHandler",
    "level": "DEBUG",
    "formatter": "simple",
    "filters": ["no_error"],
    "stream": "ext://sys.stdout",
}
stderr_handler = {
    "class": "logging.StreamHandler",
    "level": "WARNING",
    "formatter": "simple",
    "stream": "ext://sys.stderr",
}


def get_logging_setup(use_cloud_handler=False):
    handlers = {
        "stdout": stdout_handler,
        "stderr": stderr_handler,
    }
    if use_cloud_handler:
        from google.cloud.logging import Client

        cloud_client = Client()
        cloud_handler = {
            "class": "google.cloud.logging.handlers.CloudLoggingHandler",
            "client": cloud_client,
            "level": "DEBUG",
        }
        handlers = {"cloud_handler": cloud_handler}

    root_handlers = list(handlers.keys())

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "filters": filters,
        "handlers": handlers,
        "loggers": {
            "root": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "handlers": root_handlers,
            },
            "diagrams_assistant": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "handlers": root_handlers,
                "propagate": False,
            },
        },
    }
    return config


LOGGING = get_logging_setup(use_cloud_handler=False)
