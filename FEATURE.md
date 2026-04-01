# feature/message-react

Adds `Message.react()` and `Message.unreact()` so you can react to any message
with a single awaitable method call, without writing raw TL requests.

## Usage

```python
# Standard emoji reaction
await message.react("👍")

# Custom emoji (Telegram Premium) — pass the document ID as an int
await message.react(123456789012345)

# Animated / big reaction (Premium)
await message.react("❤️", big=True)

# Add to recently-used reactions list (default True)
await message.react("🔥", add_to_recent=True)

# Remove all reactions
await message.unreact()
# or equivalently:
await message.react(None)
```

## Method signatures

```python
async def react(self, emoji, *, big=False, add_to_recent=True)
    # emoji: str   => standard emoji  e.g. "👍"
    #        int   => custom emoji document ID (Premium)
    #        None  => clear all reactions

async def unreact(self)
    # Shortcut for react(None)
```

## In a handler

```python
@client.on(events.NewMessage(incoming=True))
async def like_everything(event):
    await event.message.react("❤️")
```

## Notes

- Calls `functions.messages.SendReactionRequest` internally.
- Setting the same emoji you already set **removes** it (Telegram toggle).
- Custom emoji and big reactions require Telegram Premium.
