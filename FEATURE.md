# feature/story-event

Adds a `Story` event that fires when a contact posts, updates, or deletes a Story.

## Import

```python
from telethon import events
```

## Basic usage

```python
@client.on(events.Story())
async def on_story(event):
    if event.deleted:
        print(f"{event.sender_id} deleted story {event.story_id}")
    else:
        print(f"New story from {event.sender_id}: expires {event.expire_date}")
```

## Filter options

```python
# Only new/updated stories
@client.on(events.Story(added=True))
async def new_story(event):
    print(f"Caption: {event.caption}")

# Only deletions
@client.on(events.Story(deleted=True))
async def gone(event):
    print(f"Story {event.story_id} was deleted")

# Only from specific users
@client.on(events.Story(from_users=["mycontact"]))
async def contact_story(event):
    sender = await event.get_sender()
    print(sender.first_name)
```

## Event attributes

| Attribute | Type | Description |
|---|---|---|
| `event.story_id` | `int` | Unique ID of the story |
| `event.sender_id` | `int` | Author's user ID |
| `event.media` | `MessageMedia or None` | Photo or video media |
| `event.caption` | `str` | Story caption text |
| `event.expire_date` | `datetime` | When the story expires (24 h after posting) |
| `event.deleted` | `bool` | `True` when this is a deletion event |
| `await event.get_sender()` | `User` | Fetches the full User object |

## Filter parameters

| Parameter | Description |
|---|---|
| `added` | `True` = only new/updated stories |
| `deleted` | `True` = only deletions |
| `from_users` | Whitelist of usernames / user IDs |
