# feature/scheduled-messages

Adds `get_scheduled_messages()` and `delete_scheduled_messages()` to
`TelegramClient` for managing server-side scheduled messages.

## List scheduled messages

```python
scheduled = await client.get_scheduled_messages(chat)
for msg in scheduled:
    print(f"  [{msg.id}] scheduled for {msg.date} — {msg.text!r}")
```

Returns `list[Message]` — the same rich objects as `get_messages`.

## Delete scheduled messages

```python
# Single ID
await client.delete_scheduled_messages(chat, 12345)

# Multiple IDs
await client.delete_scheduled_messages(chat, [12345, 67890])

# Delete everything in the queue
scheduled = await client.get_scheduled_messages(chat)
if scheduled:
    await client.delete_scheduled_messages(chat, [m.id for m in scheduled])
```

## Scheduling a new message

Scheduling is already supported by `send_message` via the `schedule` parameter:

```python
from datetime import datetime, timezone, timedelta

when = datetime.now(tz=timezone.utc) + timedelta(hours=1)
await client.send_message(chat, "See you in an hour!", schedule=when)
```

## Notes

- `get_scheduled_messages` always fetches from the server (no local cache).
- Accepts any resolvable `entity`: username, int ID, `InputPeer`, `Dialog`.
- Deleting a non-existent ID is silently ignored by Telegram.
