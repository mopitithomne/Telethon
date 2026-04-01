# feature/session-stats

Automatically tracks every RPC call made during a session and prints a
summary table to stderr when the client disconnects.

## What it looks like

When your bot stops (or calls `client.disconnect()`), this is printed:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Session Statistics
  Duration   : 4h 23m 11s
  Total calls: 3,842

  Method                                    Calls
  ----------------------------------------  ------
  GetHistoryRequest                          1,204
  SendMessageRequest                           823
  GetMessagesRequest                           415
  SearchGlobalRequest                          310
  GetFullChatRequest                           209
  ReadHistoryRequest                           188
  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Zero configuration needed

Stats are collected automatically. Just run your bot normally and the table
prints when it shuts down.

## Read stats programmatically

The current counters are always available via `client.session_stats`:

```python
# Top 5 most-used methods so far
for method, count in client.session_stats.most_common(5):
    print(f"{method}: {count}")

# Check a specific method
print("Send calls:", client.session_stats["SendMessageRequest"])
```

`client.session_stats` returns a `collections.Counter` snapshot (a copy,
so it will not change under you).

## Reset the counter mid-session

```python
client._session_stats.clear()
client._session_start = time.time()
```

## Log to a file instead of stderr

Redirect stderr before starting:

```python
import sys
sys.stderr = open("session.log", "a")
await client.start()
```

## How it works

- `TelegramBaseClient.__init__` initialises `self._session_stats = Counter()`
  and `self._session_start = time.time()`.
- `UserMethods.__call__` increments the counter with the class name of the
  request before delegating to `_call`. Batch requests (lists) are counted
  per-item.
- `_disconnect_coro()` calls `_print_session_stats()` before closing the
  session, so the table is always printed exactly once per session.

## Files changed

| File | Change |
|---|---|
| `telethon/client/telegrambaseclient.py` | `_session_stats`, `_session_start` attrs; `session_stats` property; `_print_session_stats()` method; hook in `_disconnect_coro()` |
| `telethon/client/users.py` | `__call__` increments the counter |
