# feature/message-translate

Exposes Telegram's built-in translation API via `message.translate()` and two
`TelegramClient` methods.

> **Note**: Telegram's translation API is available to Premium subscribers
> and may return errors for standard accounts on some endpoints.

## `message.translate(to_lang)`

```python
@client.on(events.NewMessage(incoming=True))
async def auto_translate(event):
    translated = await event.message.translate("en")
    print(translated)   # plain text string
```

## `client.translate_message(entity, message, to_lang)`

```python
# By message ID
text = await client.translate_message(chat, 42, "es")

# By Message object
text = await client.translate_message(chat, msg_object, "fr")
```

## `client.translate_text(text, to_lang, from_lang=None)`

Translate an arbitrary string that is not a chat message:

```python
result = await client.translate_text("Hello world", "fr")
print(result)   # "Bonjour le monde"

# Hint the source language for better accuracy
result = await client.translate_text("Ciao", "en", from_lang="it")
```

## Language codes

Standard IETF BCP-47 short codes: `"en"`, `"es"`, `"fr"`, `"de"`, `"ru"`,
`"zh"`, `"ja"`, `"ar"`, `"pt"`, `"it"`, `"ko"`, etc.
