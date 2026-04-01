# feature/ascii-banner

Prints a large ASCII art banner to stdout the first time the client connects
to Telegram. It shows only once per client instance (not on reconnects or
DC migrations) and is trivial to suppress.

## Output

When your bot starts, you'll see:

```
  ████████╗███████╗██╗     ███████╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗
  ╚══██╔══╝██╔════╝██║     ██╔════╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║
     ██║   █████╗  ██║     █████╗     ██║   ███████║██║   ██║██╔██╗ ██║
     ██║   ██╔══╝  ██║     ██╔══╝     ██║   ██╔══██║██║   ██║██║╚██╗██║
     ██║   ███████╗███████╗███████╗   ██║   ██║  ██║╚██████╔╝██║ ╚████║
     ╚═╝   ╚══════╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝

              Async MTProto API framework  •  Python Telegram Library
                                  v1.x.x
```

## Suppress / disable

```python
client = TelegramClient(...)
client.show_banner = False   # set before client.start()
await client.start()
```

## Print manually at any time

```python
from telethon.contrib.banner import print_banner

print_banner()
```

## How it works

- `TelegramBaseClient` gains two attributes: `show_banner = True` and
  `_banner_shown = False`.
- At the end of `connect()` (after `_updates_handle` and `_keepalive_handle`
  are created, meaning a fresh connection was established), the banner
  is printed once and `_banner_shown` is set to `True`.
- Reconnects and DC migrations reuse the same `_sender`, so `connect()`
  returns early before reaching the banner code; the flag is never reset.
- The import of `contrib.banner` is deferred (inside `connect`) so the
  module is only loaded when actually needed.

## Files changed

| File | Change |
|---|---|
| `telethon/contrib/banner.py` | New file — `print_banner()` function |
| `telethon/client/telegrambaseclient.py` | `show_banner`, `_banner_shown` attrs + `connect()` hook |
