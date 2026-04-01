# feature/prometheus-metrics

Wraps the client to expose Prometheus metrics about Telegram API usage.
Requires `pip install prometheus_client`; silently no-ops if absent.

## Quick start

```python
from telethon.contrib.metrics import TelethonMetrics

metrics = TelethonMetrics(client)
await metrics.start_server(port=9090)   # starts /metrics HTTP endpoint

await client.start()
```

Visit `http://localhost:9090/metrics` to scrape.

## Exposed metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `telethon_rpc_calls_total` | Counter | `method` | Successful calls per TL class name |
| `telethon_rpc_errors_total` | Counter | `method`, `error` | Errors by method and exception type |
| `telethon_flood_waits_total` | Counter | `method` | FloodWait sleeps triggered |
| `telethon_flood_wait_seconds_total` | Counter | `method` | Total seconds in FloodWait sleeps |
| `telethon_reconnects_total` | Counter | — | Connection re-establishments |
| `telethon_updates_queue_depth` | Gauge | — | Items pending in the updates queue |
| `telethon_connected` | Gauge | — | `1` = connected, `0` = disconnected |

## Useful PromQL

```promql
# Error rate over last 5 min
rate(telethon_rpc_errors_total[5m])

# How much time FloodWait is costing
rate(telethon_flood_wait_seconds_total[5m])

# Queue lag
telethon_updates_queue_depth
```

## Notes

- Call `metrics.start_server()` **before** `client.start()`.
- A background loop refreshes `connected` and `updates_queue_depth` every second.
- All metric operations silently no-op when `prometheus_client` is not installed.
