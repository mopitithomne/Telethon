# feature/one-shot-wait-for

Adds `client.wait_for(event, timeout=None)` — a one-shot coroutine that
suspends until a single matching event fires, then returns it and removes
the temporary handler automatically.

## Quick start

```python
from telethon import events
import asyncio

@client.on(events.NewMessage(pattern="/start"))
async def cmd_start(event):
    await event.respond("Send me any number:")
    try:
        reply = await client.wait_for(
            events.NewMessage(from_users=event.sender_id, incoming=True),
            timeout=30,
        )
        await reply.respond(f"You sent: {reply.text}")
    except asyncio.TimeoutError:
        await event.respond("Timed out — try /start again.")
```

## Wait for a button click

```python
from telethon import Button

await client.send_message(chat, "Confirm?", buttons=[
    Button.inline("Yes", b"yes"),
    Button.inline("No",  b"no"),
])

try:
    click = await client.wait_for(events.CallbackQuery(data=b"yes"), timeout=60)
    await click.answer("Confirmed!")
except asyncio.TimeoutError:
    await client.send_message(chat, "Timed out.")
```

## Signature

```python
await client.wait_for(event, *, timeout=None)
```

| Parameter | Type | Description |
|---|---|---|
| `event` | `EventBuilder` or `type` | The event to wait for. Accepts an instance or a bare class. |
| `timeout` | `float or None` | Seconds to wait; raises `asyncio.TimeoutError` on expiry. Default: wait forever. |

Returns the matched event object.

## How it works

1. An `asyncio.Future` is created.
2. A temporary handler is registered with `add_event_handler`.
3. On first match, the handler sets the future's result then raises `StopPropagation`.
4. `asyncio.shield(fut)` prevents a timeout cancellation from killing the future
   while a concurrent dispatch might still resolve it.
5. `finally` always calls `remove_event_handler`, even on timeout or exception.

## Notes

- For multi-step conversations use `async with client.conversation(chat)` instead.
- To race several events, combine multiple `wait_for` calls with `asyncio.wait`.
