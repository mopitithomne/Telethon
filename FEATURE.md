# feature/flood-guard

`FloodGuard` is a proactive rate-limiter that throttles outgoing RPC calls
**before** Telegram returns a `FloodWaitError`, using a sliding-window counter.

## Quick start

```python
from telethon.contrib.floodguard import FloodGuard

guard = FloodGuard(client, max_calls=30, per_seconds=10.0)
guard.attach()   # must be called before client.start()

await client.start()
```

## Per-method overrides

```python
from telethon.contrib.floodguard import FloodGuard, MethodLimit

guard = FloodGuard(
    client,
    max_calls=30,
    per_seconds=10.0,
    method_limits=[
        MethodLimit("SendMessageRequest",     max_calls=10, per_seconds=10.0),
        MethodLimit("ForwardMessagesRequest", max_calls=5,  per_seconds=10.0),
    ],
)
guard.attach()
await client.start()
```

## Throttle callback

```python
async def on_throttle(method: str, sleep_secs: float):
    print(f"Rate-limited {method} for {sleep_secs:.2f}s")

guard = FloodGuard(client, on_throttle=on_throttle)
guard.attach()
```

## How the sliding window works

1. A `deque` of call timestamps is kept per method (and one global).
2. Before each call, timestamps older than `per_seconds` are pruned.
3. If the window is full, the coroutine sleeps until the oldest entry expires.
4. A shared `asyncio.Lock` serialises window checks — preventing burst spikes.
5. The timestamp is recorded **after** the sleep to keep the window accurate.

## Combine with Telethon's built-in reactive guard

```python
# Proactive: FloodGuard prevents the error
guard = FloodGuard(client, max_calls=30, per_seconds=10.0)
guard.attach()

# Reactive: Telethon still auto-sleeps if one slips through
client.flood_sleep_threshold = 60
```
