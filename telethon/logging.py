"""
Structured JSON logging for Telethon.

Replaces the default ``logging.Formatter`` with one that emits newline-delimited
JSON records, compatible with Datadog, Loki, CloudWatch Logs, etc.

Usage – opt-in per-client
--------------------------

.. code-block:: python

    from telethon import TelegramClient
    from telethon.logging import configure_structured_logging

    configure_structured_logging()          # global – affects all loggers
    configure_structured_logging(level='DEBUG')

    client = TelegramClient(...)

Each log line will look like::

    {"ts":"2026-04-01T12:00:00.123456Z","level":"INFO","logger":"telethon","msg":"...","extra_key":"extra_val"}

Custom extra fields
-------------------

.. code-block:: python

    import logging
    logger = logging.getLogger('telethon')
    logger.info('Sending', extra={'rpc': 'SendMessageRequest', 'dc': 2})
    # → {"ts":"...","level":"INFO","logger":"telethon","msg":"Sending","rpc":"SendMessageRequest","dc":2}

Integration with TelegramClient
--------------------------------

Pass ``structured_logging=True`` to the constructor (patched in this module):

    client = TelegramClient(..., structured_logging=True)
"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional


# Fields that belong to the standard LogRecord but should NOT be repeated
# as top-level extra keys.
_SKIP_ATTRS = frozenset({
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'message', 'module',
    'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
    'relativeCreated', 'stack_info', 'thread', 'threadName',
    # internal logging implementation details
    'taskName',
})


class JsonFormatter(logging.Formatter):
    """
    Formats log records as compact single-line JSON objects.

    Example output::

        {"ts":"2026-04-01T12:00:00.000001Z","level":"INFO","logger":"telethon","msg":"Connected to DC 2"}
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict = {
            'ts': datetime.fromtimestamp(record.created, tz=timezone.utc)
                         .isoformat(timespec='microseconds')
                         .replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'msg': record.getMessage(),
        }

        # Attach any extra fields the caller passed via ``extra={}``
        for key, val in record.__dict__.items():
            if key not in _SKIP_ATTRS and not key.startswith('_'):
                payload[key] = val

        # Attach exception info if present
        if record.exc_info:
            payload['exc'] = self.formatException(record.exc_info)
        elif record.exc_text:
            payload['exc'] = record.exc_text

        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_structured_logging(
    *,
    level: str = 'INFO',
    logger_name: str = 'telethon',
    stream=None,
) -> None:
    """
    Install :class:`JsonFormatter` on the named logger (default: ``'telethon'``).

    This is **global** – once called, every handler attached to that logger will
    emit JSON.  If no handler exists yet, a :class:`logging.StreamHandler`
    writing to ``stderr`` (or ``stream``) is added automatically.

    Args:
        level:        Minimum log level string (``'DEBUG'``, ``'INFO'``, …).
        logger_name:  The logger to configure (``'telethon'`` by default).
        stream:       Output stream; defaults to ``stderr``.
    """
    import sys
    target = logging.getLogger(logger_name)
    target.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = JsonFormatter()

    if not target.handlers:
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setFormatter(formatter)
        target.addHandler(handler)
    else:
        for handler in target.handlers:
            handler.setFormatter(formatter)


def get_json_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Return a logger that already has :class:`JsonFormatter` attached.

    Useful when you want a *new* logger for your handler modules with
    structured output without touching the global Telethon logger.

    .. code-block:: python

        from telethon.logging import get_json_logger
        log = get_json_logger('mybot.handlers')
        log.info('Handler loaded', extra={'handler': 'on_new_message'})
    """
    import sys
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


# ---------------------------------------------------------------------------
# Patch TelegramClient constructor to accept ``structured_logging=True``
# ---------------------------------------------------------------------------

def _patch_client() -> None:
    """
    Monkey-patches ``TelegramBaseClient.__init__`` to accept a
    ``structured_logging`` keyword argument.  Import this module *before*
    creating any clients, or call :func:`configure_structured_logging`
    manually.
    """
    try:
        from telethon.client.telegrambaseclient import TelegramBaseClient
    except ImportError:
        return

    _orig_init = TelegramBaseClient.__init__

    def _patched_init(self, *args, structured_logging: bool = False, **kwargs):
        _orig_init(self, *args, **kwargs)
        if structured_logging:
            configure_structured_logging(logger_name='telethon')

    TelegramBaseClient.__init__ = _patched_init


_patch_client()
