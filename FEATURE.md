# feature/structured-logging

Replaces Telethon's plain-text log output with newline-delimited JSON so logs
can be ingested by Logstash, Datadog, Grafana Loki, or piped through `jq`.

## Quick start

```python
from telethon.logging import configure_structured_logging
import logging

configure_structured_logging(level=logging.INFO)

client = TelegramClient(...)
await client.start()
```

All `telethon.*` loggers now emit JSON lines:

```json
{"ts":"2026-04-01T12:00:00.123Z","level":"INFO","logger":"telethon.client.updates","msg":"Got 3 updates"}
```

## Logger for your own code

```python
from telethon.logging import get_json_logger

log = get_json_logger("mybot")
log.info("user started bot", extra={"user_id": 12345, "chat": "MyGroup"})
```

Output:
```json
{"ts":"...","level":"INFO","logger":"mybot","msg":"user started bot","user_id":12345,"chat":"MyGroup"}
```

## Log to a file

```python
configure_structured_logging(
    level=logging.DEBUG,
    stream=open("/var/log/mybot.jsonl", "a"),
)
```

## Parse with `jq`

```bash
# Only show ERRORs
tail -f /var/log/mybot.jsonl | jq 'select(.level=="ERROR")'

# Count events by logger
jq -r '.logger' /var/log/mybot.jsonl | sort | uniq -c | sort -rn
```

## `JsonFormatter` (advanced)

Use directly on any handler:

```python
from telethon.logging import JsonFormatter
import logging, sys

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.getLogger("mybot").addHandler(handler)
```

## Parameters for `configure_structured_logging`

| Parameter | Default | Description |
|---|---|---|
| `level` | `logging.INFO` | Minimum log level |
| `logger_name` | `"telethon"` | Root logger to configure |
| `stream` | `sys.stderr` | Output stream |
