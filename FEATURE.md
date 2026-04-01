# feature/reaction-event

Adds a `Reaction` event that fires whenever a user adds or removes an emoji
reaction on any message in a chat the bot can see.

## Import

```python
from telethon import events
```

`events.Reaction` is exported automatically alongside the other built-in events.

## Basic usage

```python
@client.on(events.Reaction())
async def on_react(event):
    print(f"{event.sender_id} reacted {event.emoji!r} on msg {event.msg_id}")
```

## Filter by emoji or sender

```python
@client.on(events.Reaction(emoji="👍"))
async def thumbs_up(event):
    await client.send_message(event.chat_id, "Thanks for the like!")

@client.on(events.Reaction(from_users=["alice", "bob"]))
async def vip_reaction(event):
    print(f"VIP reacted: {event.emoji}")
```

## Event attributes

| Attribute | Type | Description |
|---|---|---|
| `event.emoji` | `str or None` | Most-recent reaction emoji; `None` if all removed |
| `event.reactions` | `MessageReactions` | Full raw reactions object |
| `event.reaction_counts` | `list[ReactionCount]` | Per-emoji counts |
| `event.msg_id` | `int` | ID of the reacted-to message |
| `event.sender_id` | `int` | User who (un)reacted (from recent_reactions) |
| `await event.get_message()` | `Message` | Fetches the full message object |

## Filter options

| Parameter | Description |
|---|---|
| `emoji` | Only fire for this specific emoji string |
| `from_users` | Whitelist of usernames / user IDs |
